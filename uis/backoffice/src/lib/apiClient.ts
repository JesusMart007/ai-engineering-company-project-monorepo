import { clearToken, getToken, redirectToLogin } from "@/lib/auth";

// Empty by default: requests go to the backoffice itself, which proxies them to
// the API (see next.config.ts). Set NEXT_PUBLIC_API_URL to call the API directly.
export const API_URL = (process.env.NEXT_PUBLIC_API_URL ?? "").replace(/\/$/, "");

/**
 * URL for an API path such as "/suppliers" or "/api/incidents/analyze". Through the
 * proxy every API route lives under /api, so it never collides with a page (/suppliers, /login…).
 */
export function apiUrl(path: string): string {
  if (API_URL) return `${API_URL}${path}`;
  return path.startsWith("/api/") ? path : `/api${path}`;
}

/** Error raised for non-2xx responses; `messages` holds one readable line per problem. */
export class ApiError extends Error {
  constructor(
    public status: number,
    public messages: string[],
    /** Validation messages keyed by field name, from FastAPI's 422 `detail[].loc` or the incident manager's 400 `errors[].field`. */
    public fieldErrors: Record<string, string> = {},
  ) {
    super(messages.join(" "));
  }
}

/** Incident manager routes answer 400 `{ detail, errors: [{ field, message }] }`, already in plain Spanish. */
type FieldError = { field: string; message: string };

type ValidationIssue = { loc?: (string | number)[]; msg?: string; type?: string; ctx?: Record<string, unknown> };

function issueMessage({ msg, type, ctx }: ValidationIssue): string {
  switch (type) {
    case "missing":
      return "Campo obligatorio";
    case "string_too_short":
      return `Debe tener al menos ${ctx?.min_length} caracteres`;
    case "string_too_long":
      return `Debe tener como máximo ${ctx?.max_length} caracteres`;
    default: {
      const message = (msg ?? "Valor no válido").replace(/^Value error, /, "");
      return message === "password must be at most 72 bytes" ? "Debe tener como máximo 72 bytes" : message;
    }
  }
}

function issueField({ loc }: ValidationIssue): string | undefined {
  return (loc ?? []).find((part): part is string => typeof part === "string" && part !== "body");
}

async function toApiError(response: Response, fallback: string, labels: Record<string, string>): Promise<ApiError> {
  // 502/503/504 come from the Next.js proxy when the FastAPI service is down.
  let messages = [
    response.status >= 502 && response.status <= 504
      ? "No se pudo conectar con la API. ¿Está arrancada en el puerto 8000?"
      : `${fallback} (HTTP ${response.status})`,
  ];
  const fieldErrors: Record<string, string> = {};
  try {
    const { detail, errors } = await response.json();
    if (Array.isArray(errors)) {
      messages = errors.map(({ field, message }: FieldError) => {
        fieldErrors[field] ??= message;
        return message;
      });
    } else if (typeof detail === "string") messages = [detail];
    else if (Array.isArray(detail)) {
      messages = detail.map((issue: ValidationIssue) => {
        const field = issueField(issue);
        const message = issueMessage(issue);
        if (field) fieldErrors[field] ??= message;
        return field ? `${labels[field] ?? field}: ${message}` : message;
      });
    }
  } catch {
    /* non-JSON error body */
  }
  return new ApiError(response.status, messages, fieldErrors);
}

export type ApiOptions = Omit<RequestInit, "body"> & {
  body?: BodyInit;
  /** Sent as a JSON body. */
  json?: unknown;
  /** Send the bearer token and end the session on 401. Defaults to true. */
  auth?: boolean;
  /** Start of the error message when the API does not explain the failure. */
  fallback?: string;
  /** Human names for fields in 422 messages. */
  labels?: Record<string, string>;
};

/**
 * fetch wrapper for the Nexova API. Protected calls (the default) carry
 * `Authorization: Bearer <token>`; a 401 on them clears the token and goes to /login.
 */
export async function apiFetch(path: string, options: ApiOptions = {}): Promise<Response> {
  const { json, auth = true, fallback = "La API respondió con un error", labels = {}, ...init } = options;
  const headers = new Headers(init.headers);
  if (json !== undefined) headers.set("Content-Type", "application/json");
  if (auth) {
    const token = getToken();
    if (token) headers.set("Authorization", `Bearer ${token}`);
  }

  let response: Response;
  try {
    response = await fetch(apiUrl(path), { ...init, headers, body: json !== undefined ? JSON.stringify(json) : init.body });
  } catch {
    throw new ApiError(0, ["No se pudo conectar con la API. ¿Está arrancada?"]);
  }

  if (auth && response.status === 401) {
    clearToken();
    redirectToLogin();
    throw new ApiError(401, ["Tu sesión ha caducado. Vuelve a iniciar sesión."]);
  }
  if (!response.ok) throw await toApiError(response, fallback, labels);
  return response;
}

/** apiFetch that parses the JSON body (undefined for 204 No Content). */
export async function apiJson<T>(path: string, options?: ApiOptions): Promise<T> {
  const response = await apiFetch(path, options);
  return (response.status === 204 ? undefined : await response.json()) as T;
}

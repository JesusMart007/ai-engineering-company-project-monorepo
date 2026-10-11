import { clearToken, getToken, redirectToLogin } from "@/lib/auth";
import { ApiError, statusMessage, type ApiErrorKind } from "@/lib/errors";

export { ApiError } from "@/lib/errors";

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

/** Incident manager routes answer 400 `{ detail, errors: [{ field, message }] }`, already in plain Spanish. */
type FieldError = { field: string; message: string };

type ValidationIssue = { loc?: (string | number)[]; msg?: string; type?: string; ctx?: Record<string, unknown> };

/** Spanish text for a FastAPI/Pydantic 422 issue. Unknown types get a neutral message, never Pydantic's English. */
function issueMessage({ msg, type, ctx }: ValidationIssue): string {
  switch (type) {
    case "missing":
      return "Campo obligatorio";
    case "string_too_short":
      return `Debe tener al menos ${ctx?.min_length} caracteres`;
    case "string_too_long":
      return `Debe tener como máximo ${ctx?.max_length} caracteres`;
    case "too_short":
      return "Selecciona al menos una opción";
    case "greater_than":
      return `Debe ser mayor que ${ctx?.gt}`;
    case "enum":
    case "literal_error":
      return "Valor no permitido";
    case "extra_forbidden":
      return "Campo no permitido";
    case "date_from_datetime_parsing":
    case "date_parsing":
      return "Fecha no válida (usa el formato AAAA-MM-DD)";
    case "value_error":
      if (msg?.includes("72 bytes")) return "Debe tener como máximo 72 bytes";
      if (msg?.includes("YYYY-MM-DD")) return "Fecha no válida (usa el formato AAAA-MM-DD)";
      if (msg?.includes("email")) return "Introduce un email válido";
      return "Valor no válido";
    default:
      return "Valor no válido";
  }
}

function issueField({ loc }: ValidationIssue): string | undefined {
  return (loc ?? []).find((part): part is string => typeof part === "string" && part !== "body");
}

function failure(fallback: string, status: number, kind: ApiErrorKind = "http"): ApiError {
  return new ApiError(status, [`${fallback}. ${statusMessage(status, kind)}`], {}, kind);
}

/**
 * ApiError for a non-2xx response. Only field messages (422 `detail[]`, incident
 * 400 `errors[]`) come from the body; any other `detail` is server text and is
 * replaced by a message for the status. Callers translate the statuses they expect.
 */
async function toApiError(response: Response, fallback: string, labels: Record<string, string>): Promise<ApiError> {
  let body: { detail?: unknown; errors?: unknown } = {};
  try {
    body = await response.json();
  } catch {
    /* non-JSON error body (proxy page, plain text) */
  }
  const fieldErrors: Record<string, string> = {};
  let messages: string[] = [];
  if (Array.isArray(body?.errors)) {
    messages = body.errors.map(({ field, message }: FieldError) => {
      fieldErrors[field] ??= message;
      return message;
    });
  } else if (Array.isArray(body?.detail)) {
    messages = body.detail.map((issue: ValidationIssue) => {
      const field = issueField(issue);
      const message = issueMessage(issue);
      if (field) fieldErrors[field] ??= message;
      return field ? `${labels[field] ?? field}: ${message}` : message;
    });
  }
  if (messages.length === 0) return failure(fallback, response.status);
  return new ApiError(response.status, messages, fieldErrors);
}

/** Requests without their own `signal` are aborted after this long. */
export const DEFAULT_TIMEOUT_MS = 15_000;

export type ApiOptions = Omit<RequestInit, "body"> & {
  body?: BodyInit;
  /** Sent as a JSON body. */
  json?: unknown;
  /** Send the bearer token and end the session on 401. Defaults to true. */
  auth?: boolean;
  /** First sentence of the message when the call fails, e.g. "No se pudo guardar el proveedor". */
  fallback?: string;
  /** Human names for fields in 422 messages. */
  labels?: Record<string, string>;
};

const DEFAULT_FALLBACK = "No se pudo completar la operación";

/**
 * fetch wrapper for the Nexova API. Protected calls (the default) carry
 * `Authorization: Bearer <token>`; a 401 on them clears the token and goes to /login.
 * Every failure is an ApiError whose messages are safe to show.
 */
export async function apiFetch(path: string, options: ApiOptions = {}): Promise<Response> {
  const { json, auth = true, fallback = DEFAULT_FALLBACK, labels = {}, ...init } = options;
  const headers = new Headers(init.headers);
  if (json !== undefined) headers.set("Content-Type", "application/json");
  if (auth) {
    const token = getToken();
    if (token) headers.set("Authorization", `Bearer ${token}`);
  }

  let response: Response;
  try {
    response = await fetch(apiUrl(path), {
      ...init,
      headers,
      body: json !== undefined ? JSON.stringify(json) : init.body,
      signal: init.signal ?? AbortSignal.timeout(DEFAULT_TIMEOUT_MS),
    });
  } catch (reason) {
    const timedOut = reason instanceof DOMException && reason.name === "TimeoutError";
    throw failure(fallback, 0, timedOut ? "timeout" : "network");
  }

  if (auth && response.status === 401) {
    clearToken();
    redirectToLogin();
    throw new ApiError(401, [statusMessage(401)]);
  }
  if (!response.ok) throw await toApiError(response, fallback, labels);
  return response;
}

/** apiFetch that parses the JSON body (undefined for 204 No Content). A body that is not JSON is an ApiError too. */
export async function apiJson<T>(path: string, options: ApiOptions = {}): Promise<T> {
  const response = await apiFetch(path, options);
  if (response.status === 204) return undefined as T;
  try {
    return (await response.json()) as T;
  } catch {
    throw failure(options.fallback ?? DEFAULT_FALLBACK, response.status, "parse");
  }
}

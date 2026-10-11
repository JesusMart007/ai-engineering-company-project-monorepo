// User-facing error messages for the whole backoffice. Components never show an
// exception's own text: they call getUserMessage(error), which returns a message
// written for people (no status codes, stack traces or server internals).

export const SUPPORT_EMAIL = "contacto@nexova.com";

export const UNEXPECTED_ERROR = "Ha ocurrido un error inesperado. Inténtalo de nuevo y, si se repite, escríbenos.";

/** An error whose `message` is already safe to show to the user. */
export class UserFacingError extends Error {}

export type ApiErrorKind = "http" | "network" | "timeout" | "parse";

/** Failure of a call to the API. `messages` holds one readable line per problem. */
export class ApiError extends UserFacingError {
  constructor(
    public status: number,
    public messages: string[],
    /** Field messages, from FastAPI's 422 `detail[].loc` or the incident manager's 400 `errors[].field`. */
    public fieldErrors: Record<string, string> = {},
    public kind: ApiErrorKind = "http",
  ) {
    super(messages.join(" "));
  }
}

/** Message for a failed call when the API gives nothing safe to show. */
export function statusMessage(status: number, kind: ApiErrorKind = "http"): string {
  if (kind === "network") return "No hemos podido conectar con el servidor. Comprueba tu conexión e inténtalo de nuevo.";
  if (kind === "timeout") return "El servidor está tardando demasiado en responder. Inténtalo de nuevo en unos minutos.";
  if (kind === "parse") return "Hemos recibido una respuesta inesperada del servidor. Inténtalo de nuevo en unos minutos.";
  if (status === 401) return "Tu sesión ha caducado. Vuelve a iniciar sesión.";
  if (status === 403) return "No tienes permiso para realizar esta acción.";
  if (status === 404) return "No hemos encontrado lo que buscas. Puede que se haya eliminado.";
  if (status === 409) return "Ya existe un registro con esos datos.";
  if (status === 413) return "El archivo es demasiado grande.";
  if (status === 429) return "Has hecho demasiadas peticiones seguidas. Espera un momento e inténtalo de nuevo.";
  // 502-504 come from the Next.js proxy when the API is down.
  if (status >= 502 && status <= 504) return "El servicio no está disponible en este momento. Inténtalo de nuevo en unos minutos.";
  if (status >= 500) return "Algo ha fallado en nuestro servidor. Inténtalo de nuevo en unos minutos.";
  if (status >= 400) return "Algunos datos no son válidos. Revísalos e inténtalo de nuevo.";
  return UNEXPECTED_ERROR;
}

/** The message to show for any error caught in the UI. */
export function getUserMessage(error: unknown): string {
  if (error instanceof UserFacingError && error.message) return error.message;
  return UNEXPECTED_ERROR;
}

/** Same as getUserMessage, one line per problem (e.g. one per invalid field). */
export function getUserMessages(error: unknown): string[] {
  return error instanceof ApiError && error.messages.length > 0 ? error.messages : [getUserMessage(error)];
}

/** True if retrying the same call later may work (connection, timeout or server errors). */
export function isTransient(error: unknown): boolean {
  return error instanceof ApiError && (error.kind !== "http" || error.status >= 500);
}

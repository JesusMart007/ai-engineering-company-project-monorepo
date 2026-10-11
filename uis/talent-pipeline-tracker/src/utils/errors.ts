// User-facing error messages for the tracker. Components never show an
// exception's own text ("Failed to fetch", "Error HTTP 500"...): they call
// getUserMessage(error), which returns a message written for people.

export const SUPPORT_EMAIL = 'contacto@nexova.com';

export const UNEXPECTED_ERROR =
  'Ha ocurrido un error inesperado. Inténtalo de nuevo y, si se repite, escríbenos.';

export type ApiErrorKind = 'http' | 'network' | 'timeout' | 'parse';

/** Failure of a call to the records API; `message` is always safe to show. */
export class ApiError extends Error {
  constructor(
    message: string,
    public status: number,
    public kind: ApiErrorKind = 'http'
  ) {
    super(message);
    this.name = 'ApiError';
  }
}

export function statusMessage(status: number, kind: ApiErrorKind = 'http'): string {
  if (kind === 'network') return 'No hemos podido conectar con el servidor. Comprueba tu conexión e inténtalo de nuevo.';
  if (kind === 'timeout') return 'El servidor está tardando demasiado en responder. Inténtalo de nuevo en unos minutos.';
  if (kind === 'parse') return 'Hemos recibido una respuesta inesperada del servidor. Inténtalo de nuevo en unos minutos.';
  if (status === 404) return 'No hemos encontrado lo que buscas. Puede que se haya eliminado.';
  if (status >= 500) return 'Algo ha fallado en nuestro servidor. Inténtalo de nuevo en unos minutos.';
  if (status >= 400) return 'Algunos datos no son válidos. Revísalos e inténtalo de nuevo.';
  return UNEXPECTED_ERROR;
}

/** The message to show for any error caught in the UI. */
export function getUserMessage(error: unknown): string {
  return error instanceof ApiError ? error.message : UNEXPECTED_ERROR;
}

export function isNotFound(error: unknown): boolean {
  return error instanceof ApiError && error.status === 404;
}

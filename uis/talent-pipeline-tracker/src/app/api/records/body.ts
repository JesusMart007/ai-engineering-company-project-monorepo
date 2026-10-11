import { NextResponse } from 'next/server';

type JsonObject = Record<string, unknown>;

/**
 * The request body as a JSON object, or the 400 response to return. Only the
 * parsing is guarded: any other failure in a route is a real 500 (logged by Next).
 */
export async function readJsonObject(request: Request): Promise<JsonObject | NextResponse> {
  let body: unknown;
  try {
    body = await request.json();
  } catch {
    return NextResponse.json({ error: 'El cuerpo de la petición no es un JSON válido.' }, { status: 400 });
  }
  if (typeof body !== 'object' || body === null || Array.isArray(body)) {
    return NextResponse.json({ error: 'El cuerpo de la petición debe ser un objeto JSON.' }, { status: 400 });
  }
  return body as JsonObject;
}

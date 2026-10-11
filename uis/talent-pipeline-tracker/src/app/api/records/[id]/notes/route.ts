import { NextResponse } from 'next/server';
import { mockCandidates } from '../../store';
import { readJsonObject } from '../../body';
import { Note } from '../../../../../types/candidate';

interface Params {
  params: Promise<{ id: string }>;
}

export async function GET(request: Request, { params }: Params) {
  const { id } = await params;
  const candidate = mockCandidates.find((c) => c.id === id);

  if (!candidate) {
    return NextResponse.json(
      { error: 'Candidato no encontrado.' },
      { status: 404 }
    );
  }

  return NextResponse.json(candidate.notes || []);
}

export async function POST(request: Request, { params }: Params) {
  const { id } = await params;
  const candidate = mockCandidates.find((c) => c.id === id);

  if (!candidate) {
    return NextResponse.json(
      { error: 'Candidato no encontrado.' },
      { status: 404 }
    );
  }

  const body = await readJsonObject(request);
  if (body instanceof NextResponse) return body;

  const content = typeof body.content === 'string' ? body.content.trim() : '';
  if (!content) {
    return NextResponse.json(
      { error: 'El contenido de la nota es requerido.', errors: [{ field: 'content', message: 'La nota no puede estar vacía.' }] },
      { status: 400 }
    );
  }

  const newNote: Note = {
    id: `note-${Date.now()}`,
    content,
    createdAt: new Date().toISOString(),
  };

  if (!candidate.notes) {
    candidate.notes = [];
  }
  candidate.notes.unshift(newNote);

  return NextResponse.json(newNote, { status: 201 });
}

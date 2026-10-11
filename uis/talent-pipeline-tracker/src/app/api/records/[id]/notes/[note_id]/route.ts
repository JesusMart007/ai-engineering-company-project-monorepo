import { NextResponse } from 'next/server';
import { mockCandidates } from '../../../store';

interface Params {
  params: Promise<{ id: string; note_id: string }>;
}

export async function DELETE(request: Request, { params }: Params) {
  const { id, note_id } = await params;
  const candidate = mockCandidates.find((c) => c.id === id);

  if (!candidate) {
    return NextResponse.json(
      { error: 'Candidato no encontrado.' },
      { status: 404 }
    );
  }

  const notes = candidate.notes ?? [];
  const remaining = notes.filter((n) => n.id !== note_id && n.note_id !== note_id);
  if (remaining.length === notes.length) {
    return NextResponse.json({ error: 'Nota no encontrada.' }, { status: 404 });
  }
  candidate.notes = remaining;

  return new NextResponse(null, { status: 204 });
}

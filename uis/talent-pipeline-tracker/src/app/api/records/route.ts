import { NextResponse } from 'next/server';
import { mockCandidates } from './store';
import { CandidateDetail } from '../../../types/candidate';
import { readJsonObject } from './body';

const text = (value: unknown): string => (typeof value === 'string' ? value.trim() : '');

export async function GET() {
  return NextResponse.json(mockCandidates);
}

export async function POST(request: Request) {
  const body = await readJsonObject(request);
  if (body instanceof NextResponse) return body;

  const errors = [
    !text(body.name) && !text(body.full_name) && { field: 'name', message: 'El nombre es obligatorio.' },
    !text(body.email) && { field: 'email', message: 'El correo electrónico es obligatorio.' },
    !text(body.position) && !text(body.job_title) && { field: 'position', message: 'El puesto es obligatorio.' },
  ].filter(Boolean);
  if (errors.length > 0) {
    return NextResponse.json({ error: 'Faltan datos obligatorios.', errors }, { status: 400 });
  }

  const name = text(body.name) || text(body.full_name);
  const newCandidate: CandidateDetail = {
    id: `cand-${Date.now()}`,
    name,
    full_name: name,
    email: text(body.email),
    phone: text(body.phone) || text(body.phone_number),
    position: text(body.position) || text(body.job_title),
    status: text(body.status) || 'active',
    stage: text(body.stage) || 'applied',
    linkedin: text(body.linkedin) || text(body.linkedin_url),
    cv: text(body.cv) || text(body.cv_url),
    years_of_experience: Number(body.years_of_experience) || 0,
    applied_at: new Date().toISOString(),
    notes: [],
  };

  mockCandidates.unshift(newCandidate);
  return NextResponse.json(newCandidate, { status: 201 });
}

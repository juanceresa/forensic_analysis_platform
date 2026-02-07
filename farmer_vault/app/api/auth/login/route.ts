import { NextRequest, NextResponse } from 'next/server';

const COOKIE_NAME = 'vault_session';

export async function POST(request: NextRequest) {
  const body = await request.json();
  const { password } = body;

  const expected = process.env.VAULT_PASSWORD;
  if (!expected) {
    return NextResponse.json({ error: 'Auth not configured' }, { status: 500 });
  }

  if (password !== expected) {
    return NextResponse.json({ error: 'Invalid password' }, { status: 401 });
  }

  const response = NextResponse.json({ ok: true });
  response.cookies.set(COOKIE_NAME, expected, {
    httpOnly: true,
    secure: process.env.NODE_ENV === 'production',
    sameSite: 'lax',
    maxAge: 60 * 60 * 24 * 30, // 30 days
    path: '/',
  });

  return response;
}

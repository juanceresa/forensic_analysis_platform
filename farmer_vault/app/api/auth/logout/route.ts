import { NextResponse } from 'next/server';
import { SESSION_COOKIE_NAME, shouldUseSecureCookie } from '@/lib/auth';

export async function POST() {
  const response = NextResponse.json({ ok: true });
  response.cookies.set(SESSION_COOKIE_NAME, '', {
    httpOnly: true,
    secure: shouldUseSecureCookie(),
    sameSite: 'lax',
    maxAge: 0,
    path: '/',
  });
  return response;
}

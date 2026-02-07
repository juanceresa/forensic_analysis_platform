import { NextRequest, NextResponse } from 'next/server';

const COOKIE_NAME = 'vault_session';

export function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl;

  // Always allow: login page, all API routes (called internally by server components), static assets
  if (
    pathname === '/login' ||
    pathname.startsWith('/api/') ||
    pathname.startsWith('/_next/') ||
    pathname === '/favicon.ico'
  ) {
    return NextResponse.next();
  }

  // No password configured = no gate (dev mode)
  const password = process.env.VAULT_PASSWORD;
  if (!password) {
    return NextResponse.next();
  }

  // Check session cookie
  const session = request.cookies.get(COOKIE_NAME);
  if (session?.value === password) {
    return NextResponse.next();
  }

  // Redirect to login, preserving the original URL
  const loginUrl = new URL('/login', request.url);
  loginUrl.searchParams.set('next', pathname);
  return NextResponse.redirect(loginUrl);
}

export const config = {
  matcher: [
    // Match all paths except static files
    '/((?!_next/static|_next/image|favicon.ico).*)',
  ],
};

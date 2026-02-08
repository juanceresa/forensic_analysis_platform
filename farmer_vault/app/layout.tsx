import type { Metadata, Viewport } from "next";
import { IBM_Plex_Mono, Inter, JetBrains_Mono } from "next/font/google";
import "./globals.css";

// Display/Headings - Technical, authoritative
const displayFont = IBM_Plex_Mono({
  variable: "--font-display",
  subsets: ["latin"],
  weight: ["400", "500", "600"],
});

// Body text - Readable, modern
const bodyFont = Inter({
  variable: "--font-body",
  subsets: ["latin"],
});

// Data/Metrics - Tabular numbers
const monoFont = JetBrains_Mono({
  variable: "--font-mono",
  subsets: ["latin"],
  weight: ["400", "500"],
});

export const metadata: Metadata = {
  title: "Civic Table - Forensic Intelligence Platform",
  description: "Document analysis and entity intelligence for property restitution cases",
};

export const viewport: Viewport = {
  themeColor: "#020617", // slate-950
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body
        className={`${displayFont.variable} ${bodyFont.variable} ${monoFont.variable} antialiased`}
      >
        <a
          href="#main-content"
          className="sr-only focus:not-sr-only focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-cyan-400 focus-visible:ring-offset-2 focus-visible:ring-offset-slate-950 absolute left-4 top-4 z-50 rounded bg-slate-950 px-3 py-2 text-sm text-slate-100"
        >
          Skip to main content
        </a>
        <main id="main-content" className="min-h-screen">
          {children}
        </main>
      </body>
    </html>
  );
}

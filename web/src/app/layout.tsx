import type { Metadata } from "next";
import localFont from "next/font/local";
import { Suspense } from "react";

import { AccountBar } from "./account-bar";

import "./globals.css";

// Atkinson Hyperlegible keeps 0/O, 1/l/I and 5/S apart: people here check IDs, amounts
// and dates. Self-hosted (SIL OFL, see fonts/) so builds never need Google Fonts.
const sans = localFont({
  src: "./fonts/AtkinsonHyperlegibleNext-Variable.woff2",
  variable: "--font-atkinson",
  weight: "200 800",
});

const mono = localFont({
  src: "./fonts/AtkinsonHyperlegibleMono-Variable.woff2",
  variable: "--font-atkinson-mono",
  weight: "200 800",
});

export const metadata: Metadata = {
  title: { default: "Hackathon starter", template: "%s · Hackathon starter" },
  description:
    "Next.js, FastAPI, PostgreSQL with pgvector and an AI provider, wired together.",
};

export default function RootLayout({ children }: LayoutProps<"/">) {
  return (
    <html lang="en" className={`${sans.variable} ${mono.variable} antialiased`}>
      <body className="min-h-dvh font-sans">
        <Suspense fallback={null}>
          <AccountBar />
        </Suspense>
        {children}
      </body>
    </html>
  );
}

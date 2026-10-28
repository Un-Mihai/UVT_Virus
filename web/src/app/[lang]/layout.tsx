import type { Metadata } from "next";
import localFont from "next/font/local";
import { Suspense } from "react";

import { currentLocale, getDictionary } from "@/i18n/dictionary";
import { LOCALES } from "@/i18n/locales";

import { AccountBar } from "./account-bar";

import "../globals.css";

// Atkinson Hyperlegible keeps 0/O, 1/l/I and 5/S apart: people here check IDs, amounts
// and dates. Self-hosted (SIL OFL, see fonts/) so builds never need Google Fonts.
const sans = localFont({
  src: "../fonts/AtkinsonHyperlegibleNext-Variable.woff2",
  variable: "--font-atkinson",
  weight: "200 800",
});

const mono = localFont({
  src: "../fonts/AtkinsonHyperlegibleMono-Variable.woff2",
  variable: "--font-atkinson-mono",
  weight: "200 800",
});

// Cache Components needs every root parameter value listed; src/proxy.ts sends visitors to one.
export async function generateStaticParams() {
  return LOCALES.map((lang) => ({ lang }));
}

export async function generateMetadata(): Promise<Metadata> {
  const dictionary = await getDictionary();
  return {
    title: {
      default: dictionary.app.name,
      template: `%s · ${dictionary.app.name}`,
    },
    description: dictionary.app.description,
  };
}

export default async function RootLayout({ children }: LayoutProps<"/[lang]">) {
  const locale = await currentLocale();
  return (
    <html
      lang={locale}
      className={`${sans.variable} ${mono.variable} antialiased`}
    >
      <body className="min-h-dvh font-sans">
        <Suspense fallback={null}>
          <AccountBar />
        </Suspense>
        {children}
      </body>
    </html>
  );
}

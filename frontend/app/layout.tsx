import type { Metadata } from "next";
import Link from "next/link";
import { JetBrains_Mono, Inter } from "next/font/google";

import "./globals.css";

const inter = Inter({
  subsets: ["latin"],
  variable: "--font-sans",
});

const mono = JetBrains_Mono({
  subsets: ["latin"],
  variable: "--font-mono",
});

export const metadata: Metadata = {
  title: "Game Popularity Lab",
  description: "Classification and regression on Steam-adjacent game signals.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body
        className={`${inter.variable} ${mono.variable} min-h-screen font-sans antialiased`}
      >
        <div className="relative flex min-h-screen flex-col">
          <header className="sticky top-0 z-40 border-b border-border bg-background/90 backdrop-blur">
            <div className="container flex h-12 items-center justify-between gap-4">
              <Link
                href="/"
                className="font-mono text-xs font-semibold uppercase tracking-[0.2em] text-muted-foreground transition-colors hover:text-foreground"
              >
                Popularity<span className="text-foreground">Lab</span>
              </Link>
              <nav className="flex items-center gap-4 text-xs text-muted-foreground">
                <Link href="/predict?mode=classification" className="transition-colors hover:text-foreground">
                  Classify
                </Link>
                <Link href="/predict?mode=regression" className="transition-colors hover:text-foreground">
                  Regress
                </Link>
                <Link href="/whatif" className="transition-colors hover:text-foreground">
                  What-If
                </Link>
              </nav>
            </div>
          </header>
          <main className="container flex flex-1 flex-col py-8">{children}</main>
        </div>
      </body>
    </html>
  );
}

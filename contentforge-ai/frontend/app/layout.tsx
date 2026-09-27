import React from "react";
import type { Metadata } from "next";
import "@/styles/globals.css";
import { Providers } from "@/components/shared/Providers";
import { Navbar } from "@/components/shared/Navbar";

export const metadata: Metadata = {
  title: "ContentX — One Source. Every Format. Verified at Every Step.",
  description:
    "Enterprise AI information transformation and verification platform with domain intelligence, source grounding, fact registry, claim inspection, and cryptographic provenance.",
};


export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className="min-h-screen bg-slate-50 text-slate-900 flex flex-col font-sans">
        <Providers>
          <Navbar />
          <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-8">
            {children}
          </main>
        </Providers>
      </body>
    </html>
  );
}

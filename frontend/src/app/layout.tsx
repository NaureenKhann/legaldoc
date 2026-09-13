import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";
import { QueryProvider } from "@/components/providers/QueryProvider";
import { Sidebar } from "@/components/layout/Sidebar";
import { DemoModeBanner } from "@/components/shared/DemoModeBanner";

const inter = Inter({ subsets: ["latin"] });

export const metadata: Metadata = {
  title: "LegalDoc Intelligence Platform",
  description:
    "AI-powered Affidavit in Reply generation, validation, and evaluation platform",
  keywords: ["legal", "affidavit", "AI", "document generation", "validation"],
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className="dark">
      <head>
        <link rel="stylesheet" href="/output.css" />
      </head>
      <body className={`${inter.className} bg-[#0b0713] text-gray-100 antialiased`}>
        <QueryProvider>
          <DemoModeBanner />
          <div className="flex h-screen overflow-hidden">
            <Sidebar />
            <main className="flex-1 overflow-y-auto bg-[#0b0713]">
              {children}
            </main>
          </div>
        </QueryProvider>
      </body>
    </html>
  );
}

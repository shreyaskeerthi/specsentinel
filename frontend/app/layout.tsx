import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "SpecSentinel — AI Bid Risk Intelligence",
  description: "AI-powered bid risk intelligence for MEP contractors",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className="dark">
      <body className="min-h-screen bg-gray-950 antialiased">{children}</body>
    </html>
  );
}

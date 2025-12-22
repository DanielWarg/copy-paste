import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Copy/Paste - Nyhetsdesk Copilot",
  description: "RAG-powered editorial assistant",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="sv">
      <body>{children}</body>
    </html>
  );
}


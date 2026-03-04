import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";
import { SheetsProvider } from "@/lib/sheets-context";

const inter = Inter({
  subsets: ["latin"],
  variable: "--font-inter",
});

export const metadata: Metadata = {
  title: "AgentLink - Database Management",
  description: "Airtable-like interface for AgentLink Supabase data",
  icons: {
    icon: "/favicon.svg",
    apple: "/favicon.png",
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className="dark">
      <body className={`${inter.variable} font-sans antialiased`}>
        <SheetsProvider>
          {children}
        </SheetsProvider>
      </body>
    </html>
  );
}

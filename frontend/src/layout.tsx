import type { Metadata } from "next";
import { Inter } from "next/font/google";
import { ClerkProvider } from "@clerk/nextjs";
import "./globals.css";

const inter = Inter({
  subsets: ["latin"],
  variable: "--font-inter",
});

export const metadata: Metadata = {
  title: "Vatican & Colosseum Enterprise Monitor",
  description: "Enterprise monitoring dashboard for ticket agencies",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <ClerkProvider>
      <html lang="en">
        <body className={`${inter.variable} font-sans bg-[#FDFBF7] text-gray-900 min-h-screen antialiased`}>
          {children}
        </body>
      </html>
    </ClerkProvider>
  );
}

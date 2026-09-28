import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "ACER CRA Tracker",
  description: "Rating actions indexed across the seven Indian credit rating agencies.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}

import type { Metadata } from "next";
import { Inter } from "next/font/google";

import { AppProviders } from "@/components/system/app-providers";
import { cn } from "@/lib/utils";

import "./globals.css";

const inter = Inter({
  variable: "--font-sans",
  subsets: ["latin", "latin-ext"],
});

export const metadata: Metadata = {
  title: "UAV Maintenance Control",
  description: "Class, platform and mission specific UAV maintenance management",
};

export default function RootLayout({ children }: LayoutProps<"/">) {
  return (
    <html lang="tr" className={cn(inter.variable, "h-full antialiased")}>
      <body className="min-h-full bg-background font-sans text-foreground">
        <AppProviders>{children}</AppProviders>
      </body>
    </html>
  );
}

import type { Metadata } from "next";

import { LayoutShell } from "@/components/layout-shell";
import "./globals.css";

export const metadata: Metadata = {
  title: "LinkedIn Connections Dashboard",
  description: "Frontend-only internal dashboard MVP for LinkedIn connection tracking."
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>
        <LayoutShell>{children}</LayoutShell>
      </body>
    </html>
  );
}

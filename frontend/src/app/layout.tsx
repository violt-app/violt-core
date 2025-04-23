"use client";

import React from "react";
import { Providers } from "@/lib/providers";
import { Inter } from "next/font/google";
import "./globals.css";
import { WebSocketProvider } from "@/lib/websocket";
import { useRouter } from "next/navigation";

const inter = Inter({ subsets: ["latin"] });

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  const router = useRouter();

  React.useEffect(() => {
    router.push("/login");
  }, [router]);

  return (
    <html lang="en">
      <body className={inter.className}>
        <Providers>
          <WebSocketProvider>
            {children}
          </WebSocketProvider>
        </Providers>
      </body>
    </html>
  );
}

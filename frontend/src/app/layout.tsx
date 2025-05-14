"use client";

import React from "react";
import { Providers } from "@/services/providers";
import { Inter } from "next/font/google";
import "./globals.css";
import { WebSocketProvider } from "@/services/websocket";
import { Toaster } from "sonner";

const inter = Inter({ subsets: ["latin"] });

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en">
      <head>
        <link rel="icon" href="/favicon.ico" sizes="any" />
      </head>
      <body className={inter.className}>
        <Providers>
          <WebSocketProvider>
            {children}
            <Toaster />
          </WebSocketProvider>
        </Providers>
      </body>
    </html>
  );
}

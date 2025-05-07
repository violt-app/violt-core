'use client';

import { ReactNode, useEffect } from "react";
import { AuthProvider, useAuth } from "@/services/auth";
import { DeviceProvider } from "@/services/devices";
import { AutomationProvider } from "@/services/automations";
import { WebSocketProvider } from "@/services/websocket";
import { ApiProvider } from "@/services/api";
import { ErrorProvider } from "./error";

interface ProvidersProps {
  readonly children: ReactNode;
}

export function Providers({ children }: ProvidersProps) {
  return (
    <ErrorProvider>
      <AuthProvider>
        <AuthConsumer>{children}</AuthConsumer>
      </AuthProvider>
    </ErrorProvider>
  );
}

function AuthConsumer({ children }: ProvidersProps) {
  const { isLoading, checkAuth } = useAuth();
  useEffect(() => {
    checkAuth();
  }, [checkAuth]);

  if (isLoading) {
    return null;
  }

  return (
    <ApiProvider>
      <WebSocketProvider>
        <DeviceProvider>
          <AutomationProvider>
            {children}
          </AutomationProvider>
        </DeviceProvider>
      </WebSocketProvider>
    </ApiProvider>
  );
}

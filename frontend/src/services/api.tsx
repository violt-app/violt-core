/* eslint-disable @typescript-eslint/no-explicit-any */
'use client';

import {
  createContext,
  useContext,
  useState,
  ReactNode,
  useMemo,
  useCallback
} from "react";

interface ApiContextType {
  apiUrl: string;
  fetchWithAuth: (endpoint: string, options?: RequestInit) => Promise<Response>;
  getSystemStatus: () => Promise<SystemStatus>;
  getSystemStats: () => Promise<SystemStats>;
  getSystemLogs: (limit?: number) => Promise<LogEntry[]>;
}

export interface SystemStatus {
  status: string;
  version: string;
  uptime: number;
  device_count: number;
  automation_count: number;
  last_event?: Date;
  platform?: string;
  connected_clients?: number;
  isWindows?: boolean;
}

export interface SystemStats {
  cpu_usage: number;
  memory_usage: number;
  disk_usage: number;
  device_stats: Record<string, any>;
  automation_stats: Record<string, any>;
}

export interface LogEntry {
  id: string;
  timestamp: string;
  level: "info" | "warning" | "error";
  source: string;
  message: string;
  details?: Record<string, any>;
}

const ApiContext = createContext<ApiContextType | undefined>(undefined);

interface ApiProviderProps {
  readonly children: ReactNode;
}

export function ApiProvider({ children }: ApiProviderProps) {
  const [apiUrl] = useState(process.env.NEXT_PUBLIC_API_URL + "/api");

  // Helper function to fetch with authentication
  const fetchWithAuth = useCallback(async (endpoint: string, options: RequestInit = {}) => {
    const token = localStorage.getItem("authToken");

    if (!token) {
      throw new Error("Authentication required");
    }

    const headers = {
      ...options.headers,
      Authorization: `Bearer ${token}`,
    };

    const response = await fetch(`${apiUrl}${endpoint}`, {
      ...options,
      headers,
    });

    if (response.ok) {
      return response;
    } else if (response.status === 401 || response.statusText === "Unauthorized") {
      console.error("Authentication error:", response.statusText);
      // Handle authentication error
      localStorage.removeItem("authToken");
      window.location.href = "/"; // Redirect to root page
      throw new Error("Authentication required");
    } else {
      throw new Error("Failed to fetch data");
    }
  }, [apiUrl]);

  // Get system status
  const getSystemStatus = useCallback(async (): Promise<SystemStatus> => {
    try {
      const response = await fetchWithAuth("/system/status");

      if (!response.ok) {
        throw new Error("Failed to fetch system status");
      }

      const data = await response.json();
      return data;
    } catch (error) {
      console.error("Error fetching system status:", error);
      throw error;
    }
  }, [fetchWithAuth]);

  const getSystemStats = useCallback(async (): Promise<SystemStats> => {
    try {
      const response = await fetchWithAuth("/system/stats");

      if (!response.ok) {
        throw new Error("Failed to fetch system stats");
      }

      const data = await response.json();

      return data;
    } catch (error) {
      console.error("Error fetching system stats:", error);
      throw error;
    }
  }, [fetchWithAuth]);


  // Get system logs
  const getSystemLogs = useCallback(async (limit: number = 100): Promise<LogEntry[]> => {
    try {
      const response = await fetchWithAuth(`/system/logs?limit=${limit}`);

      if (!response.ok) {
        throw new Error("Failed to fetch system logs");
      }

      return await response.json();
    } catch (error) {
      console.error("Error fetching system logs:", error);
      throw error;
    }
  }, [fetchWithAuth]);

  const contextValue = useMemo(() => ({
    apiUrl,
    fetchWithAuth,
    getSystemStatus,
    getSystemStats,
    getSystemLogs,
  }), [apiUrl, fetchWithAuth, getSystemStatus, getSystemStats, getSystemLogs]);

  return (
    <ApiContext.Provider value={contextValue}>
      {children}
    </ApiContext.Provider>
  );
}

export function useApi() {
  const context = useContext(ApiContext);

  if (context === undefined) {
    throw new Error("useApi must be used within an ApiProvider");
  }

  return context;
}

/* eslint-disable @typescript-eslint/no-explicit-any */
'use client';

import {
  useCallback,
  createContext,
  useContext,
  useState,
  useEffect,
  useMemo,
  ReactNode
} from "react";
import { useError } from "./error";

interface WebSocketContextType {
  isConnected: boolean;
  lastMessage: Record<string, unknown> | null;
  socket: WebSocket | null;
  /**
   * Connect to a WebSocket endpoint. endpoint = 'devices' | 'automations' | 'events';
   * send = true will use the /ws/send/... path
   */
  connect: (endpoint: 'devices' | 'automations' | 'events', send?: boolean) => void;
  disconnect: () => void;
  sendMessage: (message: any) => void;
}

const WebSocketContext = createContext<WebSocketContextType | undefined>(undefined);

interface WebSocketProviderProps {
  readonly children: ReactNode;
}

export function WebSocketProvider({ children }: WebSocketProviderProps) {
  const [socket, setSocket] = useState<WebSocket | null>(null);
  const [isConnected, setIsConnected] = useState(false);
  const [lastMessage, setLastMessage] = useState<Record<string, unknown> | null>(null);
  const [reconnectAttempts, setReconnectAttempts] = useState(0);
  const { setError } = useError();

  const connect = useCallback((endpoint: 'devices' | 'automations' | 'events', send = false) => {
    if (socket !== null || isConnected) return;

    const token = localStorage.getItem("authToken");
    if (!token) {
      console.log("Waiting for authentication token to connect to WebSocket");
      return;
    }

    // const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    // const host = window.location.host;
    // choose path: send ? /ws/send/:endpoint : /ws/:endpoint
    const pathPrefix = send ? 'send/' : '';
    // const wsUrl = `${protocol}//${host}/ws/${pathPrefix}${endpoint}?token=${token}`;
    const wsUrl = `${process.env.NEXT_PUBLIC_API_URL}/ws/${pathPrefix}${endpoint}?token=${token}`;

    console.log("Connecting to WebSocket:", wsUrl);

    const ws = new WebSocket(wsUrl);

    ws.onopen = () => {
      setIsConnected(true);
      setReconnectAttempts(0);
    };

    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        console.log("Received WebSocket message:", data);
        setLastMessage(data);
      } catch (error) {
        console.error("Error parsing WebSocket message:", error);
        setError("Error parsing WebSocket message", error instanceof Error ? error : undefined);
      }
    };

    ws.onclose = (event) => {
      console.log(`WebSocket closed: code=${event.code}, reason=${event.reason}, wasClean=${event.wasClean}`);
      setIsConnected(false);
      setSocket(null);

      if (reconnectAttempts < 5) {
        const delay = Math.min(1000 * 2 ** reconnectAttempts, 30000);
        setReconnectAttempts((prev) => prev + 1);
        setTimeout(() => {
          connect(endpoint, send);
        }, delay);
      } else {
        console.error("Max reconnect attempts reached. WebSocket will not reconnect.");
      }
    };

    ws.onerror = (event) => {
      console.error("WebSocket error occurred:", event);
      // Error events don’t provide details beyond isTrusted; inspect onclose for code and reason
      ws.close();
    };

    setSocket(ws);
  }, [socket, isConnected, reconnectAttempts, setError]);

  const disconnect = useCallback(() => {
    if (socket) {
      socket.onclose = null; // Prevent triggering reconnect logic on manual disconnect
      socket.close();
      setSocket(null);
      setIsConnected(false);
    }
  }, [socket]);

  useEffect(() => {
    const handleStorageChange = (e: StorageEvent) => {
      if (e.key === "authToken") {
        disconnect();
        if (e.newValue) {
          connect('devices');
        }
      }
    };

    window.addEventListener("storage", handleStorageChange);

    // auto-connect to devices channel on mount if authenticated
    if (localStorage.getItem("authToken")) {
      connect('devices');
    }

    return () => {
      window.removeEventListener("storage", handleStorageChange);
      disconnect();
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const sendMessage = useCallback((message: any) => {
    if (socket && isConnected) {
      socket.send(JSON.stringify(message));
      console.log("Sent message:", message);
    } else {
      console.error("Cannot send message: WebSocket not connected");
    }
  }, [socket, isConnected]);

  const contextValue = useMemo(() => ({
    isConnected,
    lastMessage,
    socket,
    connect,
    disconnect,
    sendMessage
  }), [isConnected, lastMessage, socket, connect, disconnect, sendMessage]);

  return (
    <WebSocketContext.Provider value={contextValue}>
      {children}
    </WebSocketContext.Provider>
  );
}

export function useWebSocket() {
  const context = useContext(WebSocketContext);

  if (context === undefined) {
    throw new Error("useWebSocket must be used within a WebSocketProvider");
  }

  return context;
}

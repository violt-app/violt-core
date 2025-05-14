'use client';

import { AutomationInput } from "@/types/automation-input-type";
import { Automation } from "@/types/automation-type";
import { createContext, useContext, useState, useEffect, useCallback, ReactNode } from "react";
import { useError } from "./error";

interface AutomationContextType {
  automations: Automation[];
  isLoading: boolean;
  //error: string | null;
  fetchAutomations: () => Promise<void>;
  getAutomation: (id: string) => Automation | undefined;
  addAutomation: (automation: AutomationInput) => Promise<Automation>;
  updateAutomation: (id: string, automation: AutomationInput) => Promise<Automation>;
  deleteAutomation: (id: string) => Promise<void>;
  toggleAutomation: (id: string, enabled: boolean) => Promise<void>;
  duplicateAutomation: (id: string) => Promise<Automation>;
}

const AutomationContext = createContext<AutomationContextType | undefined>(undefined);

interface AutomationProviderProps {
  readonly children: ReactNode;
}

export function AutomationProvider({ children }: AutomationProviderProps) {
  const [automations, setAutomations] = useState<Automation[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const { setError, clearError } = useError();

  const fetchAutomations = useCallback(async () => {
    setIsLoading(true);
    clearError();

    try {
      const token = localStorage.getItem("authToken");

      if (!token) {
        setError("Authentication required");
        throw new Error("Authentication required");
      }

      const response = await fetch(process.env.NEXT_PUBLIC_API_URL + "/api/automations", {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });

      if (!response.ok) {
        setError("Failed to fetch automations");
        throw new Error("Failed to fetch automations");
      }

      const data = await response.json();
      setAutomations(data);
    } catch (error) {
      console.error("Error fetching automations:", error);
      setError(error instanceof Error ? error.message : "An unknown error occurred");
    } finally {
      setIsLoading(false);
    }
  }, [setError, clearError]);

  const getAutomation = (id: string) => {
    return automations.find(automation => automation.id === id);
  };

  const addAutomation = useCallback(async (automation: AutomationInput): Promise<Automation> => {
    setIsLoading(true);
    clearError();

    try {
      const token = localStorage.getItem("authToken");

      if (!token) {
        setError("Authentication required");
        throw new Error("Authentication required");
      }

      const response = await fetch(process.env.NEXT_PUBLIC_API_URL + "/api/automations", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify(automation),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.message || "Failed to add automation");
      }

      const newAutomation = await response.json();
      setAutomations(prev => [...prev, newAutomation]);
      return newAutomation;
    } catch (error) {
      console.error("Error adding automation:", error);
      setError(error instanceof Error ? error.message : "An unknown error occurred");
      throw error;
    } finally {
      setIsLoading(false);
    }
  }, []);

  const updateAutomation = async (id: string, automation: AutomationInput): Promise<Automation> => {
    setIsLoading(true);
    setError(null);

    try {
      const token = localStorage.getItem("authToken");

      if (!token) {
        throw new Error("Authentication required");
      }

      const response = await fetch(process.env.NEXT_PUBLIC_API_URL + `/api/automations/${id}`, {
        method: "PUT",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify(automation),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.message || "Failed to update automation");
      }

      const updatedAutomation = await response.json();
      setAutomations(prev => prev.map(a => a.id === id ? updatedAutomation : a));
      return updatedAutomation;
    } catch (error) {
      console.error("Error updating automation:", error);
      setError(error instanceof Error ? error.message : "An unknown error occurred");
      throw error;
    } finally {
      setIsLoading(false);
    }
  };

  const deleteAutomation = async (id: string): Promise<void> => {
    setIsLoading(true);
    setError(null);

    try {
      const token = localStorage.getItem("authToken");

      if (!token) {
        throw new Error("Authentication required");
      }

      const response = await fetch(process.env.NEXT_PUBLIC_API_URL + `/api/automations/${id}`, {
        method: "DELETE",
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.message || "Failed to delete automation");
      }

      setAutomations(prev => prev.filter(a => a.id !== id));
    } catch (error) {
      console.error("Error deleting automation:", error);
      setError(error instanceof Error ? error.message : "An unknown error occurred");
      throw error;
    } finally {
      setIsLoading(false);
    }
  };

  const toggleAutomation = async (id: string, enabled: boolean): Promise<void> => {
    setError(null);

    try {
      const token = localStorage.getItem("authToken");

      if (!token) {
        throw new Error("Authentication required");
      }

      const response = await fetch(process.env.NEXT_PUBLIC_API_URL + `/api/automations/${id}/toggle`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({ enabled }),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.message || "Failed to toggle automation");
      }

      // Update local state
      setAutomations(prev => prev.map(a => {
        if (a.id === id) {
          return { ...a, enabled };
        }
        return a;
      }));
    } catch (error) {
      console.error("Error toggling automation:", error);
      setError(error instanceof Error ? error.message : "An unknown error occurred");
      throw error;
    }
  };

  const duplicateAutomation = async (id: string): Promise<Automation> => {
    setIsLoading(true);
    setError(null);

    try {
      const token = localStorage.getItem("authToken");

      if (!token) {
        throw new Error("Authentication required");
      }

      const response = await fetch(process.env.NEXT_PUBLIC_API_URL + `/api/automations/${id}/duplicate`, {
        method: "POST",
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.message || "Failed to duplicate automation");
      }

      const newAutomation = await response.json();
      setAutomations(prev => [...prev, newAutomation]);
      return newAutomation;
    } catch (error) {
      console.error("Error duplicating automation:", error);
      setError(error instanceof Error ? error.message : "An unknown error occurred");
      throw error;
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    // Fetch automations on initial load if user is authenticated
    const token = localStorage.getItem("authToken");
    if (token) {
      fetchAutomations();
    }
  }, []);

  return (
    <AutomationContext.Provider
      value={{
        automations,
        isLoading,
        //error,
        fetchAutomations,
        getAutomation,
        addAutomation,
        updateAutomation,
        deleteAutomation,
        toggleAutomation,
        duplicateAutomation
      }}
    >
      {children}
    </AutomationContext.Provider>
  );
}

export function useAutomations() {
  const context = useContext(AutomationContext);

  if (context === undefined) {
    throw new Error("useAutomations must be used within an AutomationProvider");
  }

  return context;
}

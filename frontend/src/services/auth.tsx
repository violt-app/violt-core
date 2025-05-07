/* eslint-disable @typescript-eslint/no-explicit-any */
'use client';

import { createContext, useContext, useState, ReactNode, useCallback } from "react";
import { useRouter } from "next/navigation";
import { User } from "@/types/user-type";
import { useError } from "@/services/error"

interface AuthContextType {
  user: User | null;
  isLoading: boolean;
  isAuthenticated: boolean;
  login: (username: string, password: string) => Promise<void>;
  register: (user: User) => Promise<void>;
  logout: () => void;
  checkAuth: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

interface AuthProviderProps {
  readonly children: ReactNode;
}

export function AuthProvider({ children }: AuthProviderProps) {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  const [isAuthenticated, setIsAuthenticated] = useState(false);

  const router = useRouter();
  const { setError, clearError } = useError();

  const checkAuth = useCallback(async () => {
    try {
      const token = localStorage.getItem("authToken");

      if (!token) {
        setIsLoading(false);
        setIsAuthenticated(false);
        return;
      }

      const response = await fetch(process.env.NEXT_PUBLIC_API_URL + "/api/auth/me", {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });

      if (response.ok) {
        const userData = await response.json();
        setUser(userData);
        setIsAuthenticated(true);
      } else {
        //setError("Failed to fetch user data");
        localStorage.removeItem("authToken");
      }
    } catch (e: any) {
      setError("Authentication check failed: " + e.message);
    } finally {
      setIsLoading(false);
    }
  }, [setError]);

  const login = async (username: string, password: string) => {
    setIsLoading(true);
    clearError();

    try {
      const response = await fetch(process.env.NEXT_PUBLIC_API_URL + "/api/auth/login", {
        method: "POST",
        headers: {
          "Content-Type": "application/x-www-form-urlencoded",
        },
        body: new URLSearchParams({
          username: username,
          password: password,
        })
      });

      let responseData;
      try {
        responseData = await response.json();
      } catch (e) {
        console.error("Error parsing login response JSON:", e);
        throw new Error("Failed to parse server response.");
      }

      if (response.status === 401) {
        //setError("Invalid username or password");
        setIsAuthenticated(false);
        throw new Error("Invalid username or password.");
      }

      if (!response.ok) {
        setError(responseData.message);
        setIsAuthenticated(false);
        throw new Error(responseData.message);
      }

      localStorage.setItem("authToken", responseData.access_token);
      setUser(responseData.user);
      setIsAuthenticated(true);
      router.push("/dashboard");
    } catch (e: any) {
      setError(e.message);
      setIsAuthenticated(false);
      throw new Error(e.message);
    } finally {
      setIsLoading(false);
    }
  };

  const register = async (user: User) => {
    setIsLoading(true);
    clearError();

    try {
      const response = await fetch(process.env.NEXT_PUBLIC_API_URL + "/api/auth/register", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          name: user.name,
          username: user.username,
          email: user.email,
          password: user.password,
          terms_accepted: user.terms_accepted,
        }),
      });

      let responseData;
      try {
        responseData = await response.json();
      } catch (e) {
        console.error("Error parsing registration response JSON:", e);
        throw new Error("Failed to parse server response.");
      }

      if (!response.ok) {
        setError(responseData.message);
        throw new Error(responseData.message);
      }

      localStorage.setItem("authToken", responseData.token);
      setUser(responseData.user);
    } catch (error: any) {
      setError(error.message);
    } finally {
      setIsLoading(false);
    }
  };

  const logout = () => {
    localStorage.removeItem("authToken");
    setUser(null);
    setIsAuthenticated(false);
    clearError();
    router.push("/login");
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        isLoading,
        isAuthenticated: !!user,
        login,
        register,
        logout,
        checkAuth
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);

  if (context === undefined) {
    throw new Error("useAuth must be used within an AuthProvider");
  }

  return context;
}

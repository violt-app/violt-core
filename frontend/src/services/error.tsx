'use client';

import { createContext, useContext, useState, ReactNode, useCallback, JSX } from "react";
import { toast } from "sonner";
import { ExclamationIcon } from "@/components/icons/exclamation-icon";

interface ErrorContext {
    errorMessage: string | null;
    setError: (message: string | null, error?: Error) => void;
    clearError: () => void;
    displayError: () => JSX.Element | null;
}

const ErrorContext = createContext<ErrorContext | undefined>(undefined);

interface ErrorProviderProps {
    readonly children: ReactNode;
}

export function ErrorProvider({ children }: ErrorProviderProps) {
    const [errorMessage, setErrorMessage] = useState<string | null>(null);

    const createErrorMessage = useCallback((message: string | null, error?: Error) => {

        if (!error) {
            toast("An error has occured.", {
                description: message,
                action: {
                    label: "OK",
                    onClick: () => console.log("Undo"),
                },
                duration: 5000,
                icon: <ExclamationIcon />,
            });
        } else if (error) {
            toast("An error has occured.", {
                description: message + " " + (error as Error).message,
                action: {
                    label: "OK",
                    onClick: () => console.log("Undo"),
                },
                duration: 5000,
                icon: <ExclamationIcon />,
            });
        }
    }, []);

    const clearError = useCallback(() => {
        setErrorMessage(null);
    }, []);

    const setError = useCallback((message: string | null, error?: Error) => {
        clearError();

        createErrorMessage(message, error);
    }, [clearError, createErrorMessage]);

    const displayError = useCallback(() => {
        if (errorMessage) {
            return (
                <div className="text-red-500 text-sm">{errorMessage}</div>
            );
        }
        return null;
    }, [errorMessage]);

    return (
        <ErrorContext.Provider value={{ errorMessage, setError, clearError, displayError }}>
            {children}
        </ErrorContext.Provider>
    );
}

export function useError() {
    const context = useContext(ErrorContext);

    if (context === undefined) {
        throw new Error("useError must be used within an ErrorProvider");
    }

    return context;
}
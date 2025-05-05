/* eslint-disable @typescript-eslint/no-explicit-any */
export interface AutomationInput {
    name: string;
    description?: string;
    enabled: boolean;
    trigger: {
        type: string;
        config: Record<string, any>;
    };
    conditions: Array<{
        type: string;
        config: Record<string, any>;
    }>;
    actions: Array<{
        type: string;
        config: Record<string, any>;
    }>;
    condition_type: "and" | "or";
}
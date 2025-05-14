/* eslint-disable @typescript-eslint/no-explicit-any */

// Define and export Condition type
export interface Condition {
    type: string;
    config: Record<string, any>;
}

// Define and export Action type
export interface Action {
    type: string;
    config: Record<string, any>;
}

export interface Automation {
    id: string;
    name: string;
    description?: string;
    enabled: boolean;
    trigger: {
        type: string;
        config: Record<string, any>;
    };
    conditions: Condition[]; // Use the exported Condition type
    actions: Action[]; // Use the exported Action type
    condition_type: "and" | "or";
    last_triggered?: string;
    trigger_type: string;
    created_at: string;
    updated_at: string;
}
'use client';

import { useState, useEffect } from "react";
import { AutomationCard } from "@/components/automations/automation-card";
import { AutomationForm } from "@/components/automations/automation-form";
import { Header } from "@/components/layout/header";
import { MainLayout } from "@/components/layout/main-layout";
import { Sidebar } from "@/components/layout/sidebar";
import { Button } from "@/components/ui/button";
import { useAutomations } from "@/lib/automations";
import { Automation } from "@/types/automation-type";

export default function AutomationsPage() {
    const { automations: fetchedAutomations, fetchAutomations, addAutomation, updateAutomation, deleteAutomation } = useAutomations();
    const [automations, setAutomations] = useState<Automation[]>([]);
    const [isAddingAutomation, setIsAddingAutomation] = useState(false);
    const [editingAutomation, setEditingAutomation] = useState<Automation | null>(null);

    useEffect(() => {
        fetchAutomations(); // Fetch automations when the page loads
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, []);

    useEffect(() => {
        setAutomations(fetchedAutomations);
    }, [fetchedAutomations]);

    const handleAddAutomation = (newAutomation: Automation) => {
        addAutomation(newAutomation).then((addedAutomation) => {
            setAutomations((prev) => [...prev, addedAutomation]);
            setIsAddingAutomation(false);
        });
    };

    const handleEditAutomation = (updatedAutomation: Automation) => {
        updateAutomation(updatedAutomation.id, updatedAutomation).then(() => {
            setAutomations((prev) =>
                prev.map((automation) => (automation.id === updatedAutomation.id ? updatedAutomation : automation))
            );
            setEditingAutomation(null);
        });
    };

    const handleDeleteAutomation = (id: string) => {
        deleteAutomation(id).then(() => {
            setAutomations((prev) => prev.filter((automation) => automation.id !== id));
        });
    };

    return (
        <MainLayout
            sidebar={<Sidebar />}
            header={<Header title="Automations" subtitle="Manage your automations" />}
        >
            <div className="p-4">
                {isAddingAutomation && (
                    <AutomationForm
                        onSubmit={handleAddAutomation}
                        onCancel={() => setIsAddingAutomation(false)}
                    />
                )}

                {editingAutomation && (
                    <AutomationForm
                        automation={editingAutomation}
                        onSubmit={handleEditAutomation}
                        onCancel={() => setEditingAutomation(null)}
                    />
                )}

                {!isAddingAutomation && !editingAutomation && (
                    <div>
                        <Button onClick={() => setIsAddingAutomation(true)}>Add Automation</Button>
                        <div className="grid gap-4 mt-4">
                            {automations.map((automation) => (
                                <AutomationCard
                                    key={automation.id}
                                    automation={automation}
                                    onEdit={(id) =>
                                        setEditingAutomation(automations.find((a) => a.id === id) || null)
                                    }
                                    onDelete={handleDeleteAutomation}
                                />
                            ))}
                        </div>
                    </div>
                )}
            </div>
        </MainLayout>
    );
}
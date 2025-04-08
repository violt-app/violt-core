'use client';

import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Switch } from "@/components/ui/switch";
import { useState } from "react";

interface AutomationCardProps {
  automation: {
    id: string;
    name: string;
    description?: string;
    enabled: boolean;
    lastTriggered?: string;
    triggerType: string;
    conditions: number;
    actions: number;
  };
  onToggle?: (id: string, enabled: boolean) => void;
  onEdit?: (id: string) => void;
  onDelete?: (id: string) => void;
  onDuplicate?: (id: string) => void;
}

export function AutomationCard({
  automation,
  onToggle,
  onEdit,
  onDelete,
  onDuplicate
}: AutomationCardProps) {
  const [isEnabled, setIsEnabled] = useState(automation.enabled);

  const handleToggle = (checked: boolean) => {
    setIsEnabled(checked);
    if (onToggle) {
      onToggle(automation.id, checked);
    }
  };

  const getTriggerIcon = () => {
    switch (automation.triggerType) {
      case "time":
        return <ClockIcon className="h-5 w-5" />;
      case "device_state":
        return <DeviceIcon className="h-5 w-5" />;
      case "sun":
        return <SunIcon className="h-5 w-5" />;
      case "event":
        return <BoltIcon className="h-5 w-5" />;
      default:
        return <AutomationIcon className="h-5 w-5" />;
    }
  };

  const formatLastTriggered = () => {
    if (!automation.lastTriggered) return "Never triggered";

    const date = new Date(automation.lastTriggered);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMins / 60);
    const diffDays = Math.floor(diffHours / 24);

    if (diffMins < 1) return "Just now";
    if (diffMins < 60) return `${diffMins} minutes ago`;
    if (diffHours < 24) return `${diffHours} hours ago`;
    if (diffDays < 7) return `${diffDays} days ago`;

    return date.toLocaleDateString();
  };

  return (
    <Card className="overflow-hidden">
      <CardHeader className="pb-2">
        <div className="flex justify-between items-start">
          <div className="flex items-center">
            <div className="mr-2 p-2 bg-primary/10 rounded-full">
              {getTriggerIcon()}
            </div>
            <div>
              <CardTitle className="text-base">{automation.name}</CardTitle>
              <CardDescription>
                {automation.description || `${automation.triggerType} trigger`}
              </CardDescription>
            </div>
          </div>
          <Switch
            checked={isEnabled}
            onCheckedChange={handleToggle}
            aria-label="Toggle automation"
          />
        </div>
      </CardHeader>
      <CardContent>
        <div className="grid gap-2">
          <div className="flex items-center justify-between text-sm">
            <span className="text-muted-foreground">Trigger Type</span>
            <Badge variant="outline">{automation.triggerType}</Badge>
          </div>
          <div className="flex items-center justify-between text-sm">
            <span className="text-muted-foreground">Conditions</span>
            <span>{automation.conditions}</span>
          </div>
          <div className="flex items-center justify-between text-sm">
            <span className="text-muted-foreground">Actions</span>
            <span>{automation.actions}</span>
          </div>
          <div className="flex items-center justify-between text-sm">
            <span className="text-muted-foreground">Last Triggered</span>
            <span>{formatLastTriggered()}</span>
          </div>
        </div>
      </CardContent>
      <CardFooter className="border-t pt-3 flex justify-between">
        <div className="flex gap-2">
          <Button variant="outline" size="sm" onClick={() => onEdit?.(automation.id)}>
            <PencilIcon className="h-4 w-4 mr-1" />
            Edit
          </Button>
          <Button variant="outline" size="sm" onClick={() => onDuplicate?.(automation.id)}>
            <CopyIcon className="h-4 w-4 mr-1" />
            Duplicate
          </Button>
        </div>
        <Button variant="outline" size="sm" onClick={() => onDelete?.(automation.id)}>
          <TrashIcon className="h-4 w-4 mr-1" />
          Remove
        </Button>
      </CardFooter>
    </Card>
  );
}

function AutomationIcon({ className }: { className?: string }) {
  return (
    <svg
      xmlns="http://www.w3.org/2000/svg"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
      className={className}
    >
      <path d="M12 2H2v10h10V2Z" />
      <path d="M22 12h-4v4h4v-4Z" />
      <path d="M6 16H2v6h4v-6Z" />
      <path d="M22 20h-4v4h4v-4Z" />
      <path d="M14 2h8v6h-8V2Z" />
      <path d="M6 12V8" />
      <path d="M12 12v4" />
      <path d="M16 12V8" />
    </svg>
  );
}

function ClockIcon({ className }: { className?: string }) {
  return (
    <svg
      xmlns="http://www.w3.org/2000/svg"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
      className={className}
    >
      <circle cx="12" cy="12" r="10" />
      <polyline points="12 6 12 12 16 14" />
    </svg>
  );
}

function DeviceIcon({ className }: { className?: string }) {
  return (
    <svg
      xmlns="http://www.w3.org/2000/svg"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
      className={className}
    >
      <rect width="20" height="14" x="2" y="3" rx="2" />
      <line x1="8" x2="16" y1="21" y2="21" />
      <line x1="12" x2="12" y1="17" y2="21" />
    </svg>
  );
}

function SunIcon({ className }: { className?: string }) {
  return (
    <svg
      xmlns="http://www.w3.org/2000/svg"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
      className={className}
    >
      <circle cx="12" cy="12" r="4" />
      <path d="M12 2v2" />
      <path d="M12 20v2" />
      <path d="m4.93 4.93 1.41 1.41" />
      <path d="m17.66 17.66 1.41 1.41" />
      <path d="M2 12h2" />
      <path d="M20 12h2" />
      <path d="m6.34 17.66-1.41 1.41" />
      <path d="m19.07 4.93-1.41 1.41" />
    </svg>
  );
}

function BoltIcon({ className }: { className?: string }) {
  return (
    <svg
      xmlns="http://www.w3.org/2000/svg"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
      className={className}
    >
      <path d="M13 2 3 14h9l-1 8 10-12h-9l1-8z" />
    </svg>
  );
}

function PencilIcon({ className }: { className?: string }) {
  return (
    <svg
      xmlns="http://www.w3.org/2000/svg"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
      className={className}
    >
      <path d="M17 3a2.85 2.83 0 1 1 4 4L7.5 20.5 2 22l1.5-5.5Z" />
      <path d="m15 5 4 4" />
    </svg>
  );
}

function CopyIcon({ className }: { className?: string }) {
  return (
    <svg
      xmlns="http://www.w3.org/2000/svg"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
      className={className}
    >
      <rect width="14" height="14" x="8" y="8" rx="2" ry="2" />
      <path d="M4 16c-1.1 0-2-.9-2-2V4c0-1.1.9-2 2-2h10c1.1 0 2 .9 2 2" />
    </svg>
  );
}

function TrashIcon({ className }: { className?: string }) {
  return (
    <svg
      xmlns="http://www.w3.org/2000/svg"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
      className={className}
    >
      <path d="M3 6h18" />
      <path d="M19 6v14c0 1-1 2-2 2H7c-1 0-2-1-2-2V6" />
      <path d="M8 6V4c0-1 1-2 2-2h4c1 0 2 1 2 2v2" />
    </svg>
  );
}

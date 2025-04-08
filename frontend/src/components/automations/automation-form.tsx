/* eslint-disable @typescript-eslint/no-explicit-any */
'use client';

import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Checkbox } from "@/components/ui/checkbox";

interface AutomationFormProps {
  automation?: {
    id?: string;
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
  };
  onSubmit: (automation: any) => void;
  onCancel: () => void;
  isLoading?: boolean;
}

export function AutomationForm({ automation, onSubmit, onCancel, isLoading = false }: AutomationFormProps) {
  const defaultAutomation = {
    name: "",
    description: "",
    enabled: true,
    trigger: {
      type: "time",
      config: {
        time: "08:00",
        days: ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
      }
    },
    conditions: [],
    actions: [{
      type: "device_command",
      config: {
        device_id: "",
        command: "turn_on",
        params: {}
      }
    }],
    condition_type: "and" as const
  };

  const [formData, setFormData] = useState(automation || defaultAutomation);
  const [activeTab, setActiveTab] = useState("trigger");

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    setFormData((prev) => ({ ...prev, [name]: value }));
  };

  const handleTriggerTypeChange = (value: string) => {
    let config = {};
    
    // Set default config based on trigger type
    switch (value) {
      case "time":
        config = {
          time: "08:00",
          days: ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
        };
        break;
      case "sun":
        config = {
          event: "sunset",
          offset_minutes: 0
        };
        break;
      case "device_state":
        config = {
          device_id: "",
          property: "power",
          operator: "==",
          value: "on"
        };
        break;
      case "event":
        config = {
          event_type: "device_added"
        };
        break;
    }
    
    setFormData((prev) => ({
      ...prev,
      trigger: {
        type: value,
        config
      }
    }));
  };

  const handleTriggerConfigChange = (name: string, value: string | number | boolean | string[]) => {
    setFormData((prev) => ({
      ...prev,
      trigger: {
        ...prev.trigger,
        config: {
          ...prev.trigger.config,
          [name]: value
        }
      }
    }));
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onSubmit({
      ...formData,
      id: automation?.id
    });
  };

  const renderTriggerConfig = () => {
    const { type, config } = formData.trigger;
    
    switch (type) {
      case "time":
        return (
          <>
            <div className="grid gap-2">
              <Label htmlFor="time">Time</Label>
              <Input
                id="time"
                type="time"
                value={config.time}
                onChange={(e) => handleTriggerConfigChange("time", e.target.value)}
              />
            </div>
            <div className="grid gap-2">
              <Label>Days</Label>
              <div className="grid grid-cols-2 gap-2">
                {["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"].map((day) => (
                  <div key={day} className="flex items-center space-x-2">
                    <Checkbox
                      id={`day-${day}`}
                      checked={config.days.includes(day)}
                      onCheckedChange={(checked) => {
                        const days = checked
                          ? [...config.days, day]
                          : config.days.filter((d: string) => d !== day);
                        handleTriggerConfigChange("days", days);
                      }}
                    />
                    <Label htmlFor={`day-${day}`} className="capitalize">
                      {day}
                    </Label>
                  </div>
                ))}
              </div>
            </div>
          </>
        );
        
      case "sun":
        return (
          <>
            <div className="grid gap-2">
              <Label htmlFor="event">Sun Event</Label>
              <Select
                value={type === "sun" && "event" in config ? config.event : ""}
                onValueChange={(value) => handleTriggerConfigChange("event", value)}
              >
                <SelectTrigger id="event">
                  <SelectValue placeholder="Select sun event" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="sunrise">Sunrise</SelectItem>
                  <SelectItem value="sunset">Sunset</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div className="grid gap-2">
              <Label htmlFor="offset_minutes">Offset (minutes)</Label>
              <Input
                id="offset_minutes"
                type="number"
                value={type === "sun" && "offset_minutes" in config ? config.offset_minutes : ""}
                onChange={(e) => handleTriggerConfigChange("offset_minutes", parseInt(e.target.value))}
              />
              <p className="text-sm text-muted-foreground">
                Positive values are after the event, negative values are before
              </p>
            </div>
          </>
        );
        
      case "device_state":
        return (
          <>
            <div className="grid gap-2">
              <Label htmlFor="device_id">Device</Label>
              <Select
                value={type === "device_state" && "device_id" in config ? config.device_id : ""}
                onValueChange={(value) => handleTriggerConfigChange("device_id", value)}
              >
                <SelectTrigger id="device_id">
                  <SelectValue placeholder="Select device" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="device1">Living Room Light</SelectItem>
                  <SelectItem value="device2">Kitchen Sensor</SelectItem>
                  <SelectItem value="device3">Bedroom Thermostat</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div className="grid gap-2">
              <Label htmlFor="property">Property</Label>
              <Input
                id="property"
                value={type === "device_state" && "property" in config ? config.property : ""}
                onChange={(e) => handleTriggerConfigChange("property", e.target.value)}
                placeholder="power, brightness, temperature, etc."
              />
            </div>
            <div className="grid gap-2">
              <Label htmlFor="operator">Operator</Label>
              <Select
                value={type === "device_state" && "operator" in config ? config.operator : ""}
                onValueChange={(value) => handleTriggerConfigChange("operator", value)}
              >
                <SelectTrigger id="operator">
                  <SelectValue placeholder="Select operator" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="==">Equals (==)</SelectItem>
                  <SelectItem value="!=">Not equals (!=)</SelectItem>
                  <SelectItem value=">">Greater than ({'>'})</SelectItem>
                  <SelectItem value=">=">Greater than or equal ({'>='})</SelectItem>
                  <SelectItem value="<">Less than ({'<'})</SelectItem>
                  <SelectItem value="<=">Less than or equal ({'<='})</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div className="grid gap-2">
              <Label htmlFor="value">Value</Label>
              <Input
                id="value"
                value={type === "device_state" && "value" in config ? config.value : ""}
                onChange={(e) => handleTriggerConfigChange("value", e.target.value)}
                placeholder="on, off, 75, etc."
              />
            </div>
          </>
        );
        
      case "event":
        return (
          <div className="grid gap-2">
            <Label htmlFor="event_type">Event Type</Label>
            <Select
              value={"event_type" in config ? config.event_type : ""}
              onValueChange={(value) => handleTriggerConfigChange("event_type", value)}
            >
              <SelectTrigger id="event_type">
                <SelectValue placeholder="Select event type" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="device_added">Device Added</SelectItem>
                <SelectItem value="device_removed">Device Removed</SelectItem>
                <SelectItem value="device_online">Device Online</SelectItem>
                <SelectItem value="device_offline">Device Offline</SelectItem>
                <SelectItem value="system_startup">System Startup</SelectItem>
              </SelectContent>
            </Select>
          </div>
        );
        
      default:
        return <p>Select a trigger type</p>;
    }
  };

  return (
    <form onSubmit={handleSubmit}>
      <Card>
        <CardHeader>
          <CardTitle>{automation?.id ? "Edit Automation" : "Create Automation"}</CardTitle>
          <CardDescription>
            {automation?.id
              ? "Update your automation rule"
              : "Create a new automation rule with triggers, conditions, and actions"}
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid gap-6">
            <div className="grid gap-4">
              <div className="grid gap-2">
                <Label htmlFor="name">Name</Label>
                <Input
                  id="name"
                  name="name"
                  placeholder="Morning Routine"
                  value={formData.name}
                  onChange={handleChange}
                  required
                />
              </div>
              
              <div className="grid gap-2">
                <Label htmlFor="description">Description (Optional)</Label>
                <Input
                  id="description"
                  name="description"
                  placeholder="Turn on lights and adjust thermostat in the morning"
                  value={formData.description}
                  onChange={handleChange}
                />
              </div>
            </div>
            
            <Tabs value={activeTab} onValueChange={setActiveTab}>
              <TabsList className="grid w-full grid-cols-3">
                <TabsTrigger value="trigger">Trigger</TabsTrigger>
                <TabsTrigger value="conditions">Conditions</TabsTrigger>
                <TabsTrigger value="actions">Actions</TabsTrigger>
              </TabsList>
              
              <TabsContent value="trigger" className="pt-4">
                <div className="grid gap-4">
                  <div className="grid gap-2">
                    <Label htmlFor="trigger_type">Trigger Type</Label>
                    <Select
                      value={formData.trigger.type}
                      onValueChange={handleTriggerTypeChange}
                    >
                      <SelectTrigger id="trigger_type">
                        <SelectValue placeholder="Select trigger type" />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="time">Time</SelectItem>
                        <SelectItem value="sun">Sun (Sunrise/Sunset)</SelectItem>
                        <SelectItem value="device_state">Device State</SelectItem>
                        <SelectItem value="event">Event</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                  
                  {renderTriggerConfig()}
                </div>
              </TabsContent>
              
              <TabsContent value="conditions" className="pt-4">
                <div className="grid gap-4">
                  <div className="grid gap-2">
                    <Label htmlFor="condition_type">Condition Type</Label>
                    <Select
                      value={formData.condition_type}
                      onValueChange={(value: "and" | "or") => 
                        setFormData((prev) => ({ ...prev, condition_type: value }))
                      }
                    >
                      <SelectTrigger id="condition_type">
                        <SelectValue placeholder="Select condition type" />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="and">AND (All conditions must match)</SelectItem>
                        <SelectItem value="or">OR (Any condition can match)</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                  
                  {formData.conditions.length === 0 ? (
                    <div className="border rounded-md p-6 flex flex-col items-center justify-center">
                      <p className="text-muted-foreground mb-4">No conditions added yet</p>
                      <Button type="button" variant="outline">
                        Add Condition
                      </Button>
                    </div>
                  ) : (
                    <div className="border rounded-md p-4">
                      <p>Conditions will be displayed here</p>
                    </div>
                  )}
                </div>
              </TabsContent>
              
              <TabsContent value="actions" className="pt-4">
                <div className="grid gap-4">
                  {formData.actions.length === 0 ? (
                    <div className="border rounded-md p-6 flex flex-col items-center justify-center">
                      <p className="text-muted-foreground mb-4">No actions added yet</p>
                      <Button type="button" variant="outline">
                        Add Action
                      </Button>
                    </div>
                  ) : (
                    <div className="border rounded-md p-4">
                      <p>Actions will be displayed here</p>
                      <Button type="button" variant="outline" className="mt-4">
                        Add Another Action
                      </Button>
                    </div>
                  )}
                </div>
              </TabsContent>
            </Tabs>
          </div>
        </CardContent>
        <CardFooter className="flex justify-between">
          <Button variant="outline" type="button" onClick={onCancel}>
            Cancel
          </Button>
          <Button type="submit" disabled={isLoading}>
            {isLoading && (
              <div className="mr-2 h-4 w-4 animate-spin rounded-full border-2 border-slate-200 border-t-slate-800"></div>
            )}
            {automation?.id ? "Update Automation" : "Create Automation"}
          </Button>
        </CardFooter>
      </Card>
    </form>
  );
}

'use client';

import { MainLayout } from "@/components/layout/main-layout";
import { Sidebar } from "@/components/layout/sidebar";
import { Header } from "@/components/layout/header";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { useDevices } from "@/lib/devices";
import { useAutomations } from "@/lib/automations";
import { useApi, SystemStatus, SystemStats } from "@/lib/api";
import { useEffect, useState } from "react";
import { useWebSocket } from "@/lib/websocket";

export default function DashboardPage() {
  // This is a client component that will be hydrated on the client side
  return <DashboardContent />;
}

function DashboardContent() {
  const { devices, isLoading: devicesLoading } = useDevices();
  const { automations, isLoading: automationsLoading } = useAutomations();
  const { getSystemStatus, getSystemStats } = useApi();

  const [systemStatus, setSystemStatus] = useState<SystemStatus | null>(null);
  const [systemStats, setSystemStats] = useState<SystemStats | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const { connect, lastMessage, sendMessage, isConnected } = useWebSocket();

  // on mount, subscribe to device updates
  useEffect(() => {
    connect('devices');               // opens /ws/devices?token=…
  }, [connect]);

  // whenever the server pushes device state
  useEffect(() => {
    if (lastMessage) {
      // update your Redux/store/local state…
      console.log('new device payload:', lastMessage);
    }
  }, [lastMessage]);

  // if you need to send a control message back
  const rebootDevice = (deviceId: string) => {
    sendMessage({ type: 'reboot', payload: { deviceId } });
  };

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [status, stats] = await Promise.all([getSystemStatus(), getSystemStats()]);
        setSystemStatus(status);
        setSystemStats(stats);
      } catch (error) {
        console.error("Failed to fetch system data:", error);
      } finally {
        setIsLoading(false);
      }
    };

    fetchData();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const onlineDevices = devices?.filter(device => device.status === "connected").length || 0;
  const enabledAutomations = automations?.filter(automation => automation.enabled).length || 0;

  console.log("System Status:", systemStatus);
  console.log("System Stats:", systemStats);
  console.log("Devices:", devices);
  console.log("Automations:", automations);
  console.log("WebSocket Connected:", isConnected);
  console.log("WebSocket Last Message:", lastMessage);
  console.log("WebSocket Send Message:", sendMessage);
  console.log("WebSocket Reboot Device:", rebootDevice);
  console.log("WebSocket Connect:", connect);
  console.log("WebSocket Is Connected:", isConnected);
  console.log("WebSocket Is Loading:", isLoading);

  return (
    <MainLayout
      sidebar={<Sidebar />}
      header={<Header title="Dashboard" subtitle="Overview of your smart home" />}
    >
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Devices</CardTitle>
            <DeviceIcon className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{devicesLoading ? "..." : devices.length}</div>
            <p className="text-xs text-muted-foreground">
              {onlineDevices} online
            </p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Automations</CardTitle>
            <AutomationIcon className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{automationsLoading ? "..." : automations.length}</div>
            <p className="text-xs text-muted-foreground">
              {enabledAutomations} enabled
            </p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">CPU Usage</CardTitle>
            <CpuIcon className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{isLoading ? "..." : `${systemStats?.cpu_usage?.toFixed(1)}%`}</div>
            <p className="text-xs text-muted-foreground">
              System load
            </p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Memory Usage</CardTitle>
            <MemoryIcon className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{isLoading ? "..." : `${systemStats?.memory_usage?.toFixed(1)}%`}</div>
            <p className="text-xs text-muted-foreground">
              Available memory
            </p>
          </CardContent>
        </Card>
      </div>

      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-7 mt-4">
        <Card className="col-span-4">
          <CardHeader>
            <CardTitle>Recent Activity</CardTitle>
            <CardDescription>
              System events and device activity
            </CardDescription>
          </CardHeader>
          <CardContent>
            {isLoading ? (
              <div className="flex items-center justify-center h-[200px]">
                <div className="h-8 w-8 animate-spin rounded-full border-4 border-primary border-t-transparent"></div>
              </div>
            ) : (
              <div className="space-y-4">
                <div className="border-b pb-2">
                  <div className="flex justify-between items-center">
                    <div>
                      <p className="font-medium">System started</p>
                      <p className="text-sm text-muted-foreground">Violt Core service initialized</p>
                    </div>
                    <div className="text-sm text-muted-foreground">{systemStatus?.uptime ?? 0}</div>
                  </div>
                </div>
                <div className="border-b pb-2">
                  <div className="flex justify-between items-center">
                    <div>
                      <p className="font-medium">Device connected</p>
                      <p className="text-sm text-muted-foreground">Number of devices connected</p>
                    </div>
                    <div className="text-sm text-muted-foreground">{systemStatus?.device_count ?? 0}</div>
                  </div>
                </div>
                <div className="border-b pb-2">
                  <div className="flex justify-between items-center">
                    <div>
                      <p className="font-medium">Automations</p>
                      <p className="text-sm text-muted-foreground">Number of automations</p>
                    </div>
                    <div className="text-sm text-muted-foreground">{systemStatus?.automation_count ?? 0}</div>
                  </div>
                </div>
              </div>
            )}
          </CardContent>
        </Card>
        <Card className="col-span-3">
          <CardHeader>
            <CardTitle>System Information</CardTitle>
            <CardDescription>
              Violt Core Lite status
            </CardDescription>
          </CardHeader>
          <CardContent>
            {isLoading ? (
              <div className="flex items-center justify-center h-[200px]">
                <div className="h-8 w-8 animate-spin rounded-full border-4 border-primary border-t-transparent"></div>
              </div>
            ) : (
              <div className="space-y-4">
                <div className="flex justify-between">
                  <div className="text-sm font-medium">Version</div>
                  <div className="text-sm">{systemStatus?.version ?? "1.0.0"}</div>
                </div>
                <div className="flex justify-between">
                  <div className="text-sm font-medium">Uptime</div>
                  <div className="text-sm">{systemStatus?.uptime ?? 0}</div>
                </div>
                <div className="flex justify-between">
                  <div className="text-sm font-medium">Disk Usage</div>
                  <div className="text-sm">{systemStats?.disk_usage?.toFixed(1) ?? 0}%</div>
                </div>
                <div className="flex justify-between">
                  <div className="text-sm font-medium">Connected Clients</div>
                  <div className="text-sm">{systemStats?.device_stats.length ?? 0}</div>
                </div>
                <div className="flex justify-between">
                  <div className="text-sm font-medium">Platform</div>
                  <div className="text-sm" style={{ textTransform: 'capitalize' }}>{systemStatus?.platform ?? (systemStatus?.isWindows ? "Windows" : "Unknown")}</div>
                </div>
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </MainLayout>
  );
}

function DeviceIcon({ className }: { readonly className?: string }) {
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

function AutomationIcon({ className }: { readonly className?: string }) {
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

function CpuIcon({ className }: { readonly className?: string }) {
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
      <rect x="4" y="4" width="16" height="16" rx="2" />
      <rect x="9" y="9" width="6" height="6" />
      <path d="M15 2v2" />
      <path d="M15 20v2" />
      <path d="M2 15h2" />
      <path d="M20 15h2" />
      <path d="M9 2v2" />
      <path d="M9 20v2" />
      <path d="M2 9h2" />
      <path d="M20 9h2" />
    </svg>
  );
}

function MemoryIcon({ className }: { readonly className?: string }) {
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
      <path d="M6 19v-3" />
      <path d="M10 19v-3" />
      <path d="M14 19v-3" />
      <path d="M18 19v-3" />
      <path d="M8 11V9" />
      <path d="M16 11V9" />
      <path d="M12 11V9" />
      <path d="M2 15h20" />
      <path d="M2 7a2 2 0 0 1 2-2h16a2 2 0 0 1 2 2v10a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V7z" />
    </svg>
  );
}

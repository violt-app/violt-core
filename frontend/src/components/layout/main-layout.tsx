import { ReactNode, SVGProps, useEffect, useState } from "react";
import { cn } from "@/services/utils";
import { SystemStats, SystemStatus, useApi } from "@/services/api";

interface MainLayoutProps {
  children: ReactNode;
  sidebar?: ReactNode;
  header?: ReactNode;
  className?: string;
}

export function MainLayout({
  children,
  sidebar,
  header,
  className,
}: MainLayoutProps) {
  const [systemStatus, setSystemStatus] = useState<SystemStatus | null>(null);
  const [systemStats, setSystemStats] = useState<SystemStats | null>(null);
  const { getSystemStatus, getSystemStats } = useApi();

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [status, stats] = await Promise.all([getSystemStatus(), getSystemStats()]);
        setSystemStatus(status);
        setSystemStats(stats);
      } catch (error) {
        console.error("Failed to fetch system data:", error);
      } finally {
        //setIsLoading(false);
      }
    };

    fetchData();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  return (
    <div className="min-h-screen bg-background flex">
      {sidebar && (
        <aside className="hidden md:flex w-64 flex-col fixed inset-y-0 z-50 border-r">
          <div className="flex flex-col flex-grow overflow-y-auto">
            {sidebar}
          </div>
        </aside>
      )}
      <div className={cn("flex flex-col flex-1", sidebar && "md:pl-64")}>
        {header && (
          <header className="sticky top-0 z-40 border-b bg-background">
            {header}
          </header>
        )}
        <div className="p-4 bg-background bg-gray-50 space-x-2">
          <div className="inline-flex items-center rounded-md bg-gray-50 px-2 py-1 text-xs font-medium text-gray-600 ring-1 ring-gray-500/10 ring-inset">
            <Status className={`h-5 w-5 ${systemStatus?.status === 'running' ? 'text-green-500' : 'text-red-500'}`} />{" "}
            <span className="text-sm text-muted-foreground">System Status</span>

          </div>
          <div className="inline-flex items-center rounded-md bg-gray-50 px-2 py-1 text-xs font-medium text-gray-600 ring-1 ring-gray-500/10 ring-inset">
            <CpuIcon className={`h-5 w-5 ${systemStats?.cpu_usage !== undefined && systemStats.cpu_usage >= 75 ? 'text-red-500' : 'text-green-500'}`} />{" "}
            <span className="text-sm text-muted-foreground">CPU Load</span>
          </div>
          <div className="inline-flex items-center rounded-md bg-gray-50 px-2 py-1 text-xs font-medium text-gray-600 ring-1 ring-gray-500/10 ring-inset">
            <DiskIcon className={`h-5 w-5 ${systemStats?.disk_usage !== undefined && systemStats.disk_usage >= 75 ? 'text-red-500' : 'text-green-500'}`} />
            <span className="text-sm text-muted-foreground">Disk Usage</span>
          </div>
          <div className="inline-flex items-center rounded-md bg-gray-50 px-2 py-1 text-xs font-medium text-gray-600 ring-1 ring-gray-500/10 ring-inset">
            <MemoryIcon className={`h-5 w-5 ${systemStats?.memory_usage !== undefined && systemStats.memory_usage >= 75 ? 'text-red-500' : 'text-green-500'}`} />
            <span className="text-sm text-muted-foreground">Memory Usage</span>
          </div>
        </div>
        <main className={cn("flex-1 p-4 md:p-6", className)}>{children}</main>
      </div>
    </div>
  );
}

export function Status(props: SVGProps<SVGSVGElement>) {
  return (
    <svg
      xmlns="http://www.w3.org/2000/svg"
      viewBox="0 0 56 56"
      width="1em"
      height="1em"
      {...props}
    >
      <title>System Status</title>
      <path
        fill="currentColor"
        d="m50.923 21.002l.046.131l.171.566l.143.508l.061.232l.1.42a23.93 23.93 0 0 1-2.653 17.167a23.93 23.93 0 0 1-13.57 10.89l-.404.12l-.496.128l-.717.17a1.89 1.89 0 0 1-2.288-1.558a2.127 2.127 0 0 1 1.606-2.389l.577-.145q.54-.142.929-.273a19.93 19.93 0 0 0 10.899-8.943a19.93 19.93 0 0 0 2.292-13.923l-.069-.313l-.092-.365l-.115-.418l-.138-.47a2.135 2.135 0 0 1 1.26-2.602a1.894 1.894 0 0 1 2.458 1.067M7.385 19.92q.065.02.128.044A2.127 2.127 0 0 1 8.78 22.55q-.27.909-.39 1.513a19.93 19.93 0 0 0 2.295 13.91a19.93 19.93 0 0 0 10.911 8.947l.306.097l.174.05l.39.106l.694.171a2.135 2.135 0 0 1 1.623 2.393a1.894 1.894 0 0 1-2.152 1.594l-.138-.025l-.576-.135l-.51-.13l-.446-.125l-.2-.06A23.93 23.93 0 0 1 7.22 39.972a23.93 23.93 0 0 1-2.647-17.197l.077-.32l.1-.375l.194-.665l.076-.25a1.89 1.89 0 0 1 2.365-1.246M28.051 12c8.837 0 16 7.163 16 16s-7.163 16-16 16s-16-7.163-16-16s7.164-16 16-16m0 4c-6.627 0-12 5.373-12 12s5.373 12 12 12c6.628 0 12-5.373 12-12s-5.372-12-12-12m0-12a23.93 23.93 0 0 1 16.217 6.306l.239.227l.275.274l.31.322l.346.369a1.89 1.89 0 0 1-.205 2.76a2.127 2.127 0 0 1-2.873-.196q-.326-.345-.605-.617l-.35-.334l-.16-.143A19.93 19.93 0 0 0 28.051 8a19.93 19.93 0 0 0-13.204 4.976l-.114.102l-.253.24l-.287.285l-.495.515c-.76.809-2.014.9-2.883.21a1.894 1.894 0 0 1-.305-2.662l.09-.106l.405-.431l.368-.378q.262-.263.484-.465A23.93 23.93 0 0 1 28.05 4"
      ></path>
    </svg>
  )
}

export function Themometer(props: SVGProps<SVGSVGElement>) {
  return (
    <svg
      xmlns="http://www.w3.org/2000/svg"
      width="20"
      height="20"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
      className="lucide lucide-thermometer-icon lucide-thermometer"
      {...props}>
      <title>System Load</title>
      <path d="M14 4v10.54a4 4 0 1 1-4 0V4a2 2 0 0 1 4 0Z" />
    </svg>
  )
}

export function DiskIcon(props: SVGProps<SVGSVGElement>) {
  return (
    <svg
      xmlns="http://www.w3.org/2000/svg"
      width="20"
      height="20"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
      className="lucide lucide-hard-drive-icon lucide-hard-drive"
      {...props}>
      <line x1="22" x2="2" y1="12" y2="12" />
      <path d="M5.45 5.11 2 12v6a2 2 0 0 0 2 2h16a2 2 0 0 0 2-2v-6l-3.45-6.89A2 2 0 0 0 16.76 4H7.24a2 2 0 0 0-1.79 1.11z" />
      <line x1="6" x2="6.01" y1="16" y2="16" />
      <line x1="10" x2="10.01" y1="16" y2="16" />
    </svg>
  );
}

export function CpuIcon(props: SVGProps<SVGSVGElement>) {
  return (
    <svg
      xmlns="http://www.w3.org/2000/svg"
      width="20"
      height="20"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
      className="lucide lucide-cpu-icon lucide-cpu"
      {...props}>
      <title>CPU Load</title>
      <path d="M12 20v2" />
      <path d="M12 2v2" />
      <path d="M17 20v2" />
      <path d="M17 2v2" />
      <path d="M2 12h2" />
      <path d="M2 17h2" />
      <path d="M2 7h2" />
      <path d="M20 12h2" />
      <path d="M20 17h2" />
      <path d="M20 7h2" />
      <path d="M7 20v2" />
      <path d="M7 2v2" />
      <rect x="4" y="4" width="16" height="16" rx="2" />
      <rect x="8" y="8" width="8" height="8" rx="1" />
    </svg>
  );
}

export function MemoryIcon(props: SVGProps<SVGSVGElement>) {
  return (
    <svg
      xmlns="http://www.w3.org/2000/svg"
      width="24" height="24"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
      className="lucide lucide-microchip-icon lucide-microchip"
      {...props}>
      <title>Memory Load</title>
      <path d="M18 12h2" />
      <path d="M18 16h2" />
      <path d="M18 20h2" />
      <path d="M18 4h2" />
      <path d="M18 8h2" />
      <path d="M4 12h2" />
      <path d="M4 16h2" />
      <path d="M4 20h2" />
      <path d="M4 4h2" />
      <path d="M4 8h2" />
      <path d="M8 2a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h8a2 2 0 0 0 2-2V4a2 2 0 0 0-2-2h-1.5c-.276 0-.494.227-.562.495a2 2 0 0 1-3.876 0C9.994 2.227 9.776 2 9.5 2z" /></svg>
  );
}
import Link from "next/link";
import { ReactNode } from "react";
import { cn } from "@/lib/utils";

interface SidebarProps {
  className?: string;
}

interface SidebarItemProps {
  href: string;
  icon: ReactNode;
  children: ReactNode;
  active?: boolean;
}

export function Sidebar({ className }: SidebarProps) {
  return (
    <div className={cn("flex flex-col h-full", className)}>
      <div className="px-3 py-4">
        <Link href="/dashboard" className="flex items-center mb-6">
          <span className="text-2xl font-bold">Violt Core</span>
          <span className="ml-2 text-xs bg-primary text-primary-foreground px-1.5 py-0.5 rounded">Lite</span>
        </Link>
        <nav className="space-y-1">
          <SidebarItem href="/dashboard" icon={<DashboardIcon />} active>
            Dashboard
          </SidebarItem>
          <SidebarItem href="/devices" icon={<DevicesIcon />}>
            Devices
          </SidebarItem>
          <SidebarItem href="/automations" icon={<AutomationsIcon />}>
            Automations
          </SidebarItem>
          <SidebarItem href="/integrations" icon={<IntegrationsIcon />}>
            Integrations
          </SidebarItem>
          <SidebarItem href="/settings" icon={<SettingsIcon />}>
            Settings
          </SidebarItem>
        </nav>
      </div>
      <div className="mt-auto p-4 border-t">
        <div className="flex items-center">
          <div className="w-8 h-8 rounded-full bg-primary flex items-center justify-center text-primary-foreground">
            U
          </div>
          <div className="ml-3">
            <p className="text-sm font-medium">User Name</p>
            <p className="text-xs text-muted-foreground">user@example.com</p>
          </div>
        </div>
      </div>
    </div>
  );
}

function SidebarItem({ href, icon, children, active }: SidebarItemProps) {
  return (
    <Link
      href={href}
      className={cn(
        "flex items-center px-3 py-2 text-sm font-medium rounded-md",
        active
          ? "bg-primary/10 text-primary"
          : "text-muted-foreground hover:bg-muted hover:text-foreground"
      )}
    >
      <span className="mr-3 h-5 w-5">{icon}</span>
      {children}
    </Link>
  );
}

function DashboardIcon() {
  return (
    <svg
      xmlns="http://www.w3.org/2000/svg"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
      className="h-5 w-5"
    >
      <rect width="7" height="9" x="3" y="3" rx="1" />
      <rect width="7" height="5" x="14" y="3" rx="1" />
      <rect width="7" height="9" x="14" y="12" rx="1" />
      <rect width="7" height="5" x="3" y="16" rx="1" />
    </svg>
  );
}

function DevicesIcon() {
  return (
    <svg
      xmlns="http://www.w3.org/2000/svg"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
      className="h-5 w-5"
    >
      <path d="M5 4h14c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H5c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2Z" />
      <path d="M12 16a2 2 0 1 0 0-4 2 2 0 0 0 0 4Z" />
      <path d="M12 4v4" />
      <path d="M4 12h4" />
      <path d="M16 12h4" />
      <path d="M12 16v4" />
    </svg>
  );
}

function AutomationsIcon() {
  return (
    <svg
      xmlns="http://www.w3.org/2000/svg"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
      className="h-5 w-5"
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

function IntegrationsIcon() {
  return (
    <svg
      xmlns="http://www.w3.org/2000/svg"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
      className="h-5 w-5"
    >
      <path d="M3.8 9a16.5 16.5 0 0 0 4.2 7" />
      <path d="M9 3.8a16.5 16.5 0 0 1 7 4.2" />
      <path d="M20.2 9a16.5 16.5 0 0 1-4.2 7" />
      <path d="M15 20.2a16.5 16.5 0 0 0-7-4.2" />
      <circle cx="12" cy="12" r="3" />
    </svg>
  );
}

function SettingsIcon() {
  return (
    <svg
      xmlns="http://www.w3.org/2000/svg"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
      className="h-5 w-5"
    >
      <path d="M12.22 2h-.44a2 2 0 0 0-2 2v.18a2 2 0 0 1-1 1.73l-.43.25a2 2 0 0 1-2 0l-.15-.08a2 2 0 0 0-2.73.73l-.22.38a2 2 0 0 0 .73 2.73l.15.1a2 2 0 0 1 1 1.72v.51a2 2 0 0 1-1 1.74l-.15.09a2 2 0 0 0-.73 2.73l.22.38a2 2 0 0 0 2.73.73l.15-.08a2 2 0 0 1 2 0l.43.25a2 2 0 0 1 1 1.73V20a2 2 0 0 0 2 2h.44a2 2 0 0 0 2-2v-.18a2 2 0 0 1 1-1.73l.43-.25a2 2 0 0 1 2 0l.15.08a2 2 0 0 0 2.73-.73l.22-.39a2 2 0 0 0-.73-2.73l-.15-.08a2 2 0 0 1-1-1.74v-.5a2 2 0 0 1 1-1.74l.15-.09a2 2 0 0 0 .73-2.73l-.22-.38a2 2 0 0 0-2.73-.73l-.15.08a2 2 0 0 1-2 0l-.43-.25a2 2 0 0 1-1-1.73V4a2 2 0 0 0-2-2z" />
      <circle cx="12" cy="12" r="3" />
    </svg>
  );
}

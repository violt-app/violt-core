import { ReactNode } from "react";
import { cn } from "@/lib/utils";

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
        <main className={cn("flex-1 p-4 md:p-6", className)}>{children}</main>
      </div>
    </div>
  );
}

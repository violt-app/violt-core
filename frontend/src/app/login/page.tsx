'use client';

import { useAuth } from "@/lib/auth";
import { UserAuthForm } from "@/components/auth/user-auth-form";
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card";
import Link from "next/link";
import { useEffect } from "react";
import { useRouter } from "next/navigation";

export default function LoginPage() {
  const { isAuthenticated, isLoading } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (isAuthenticated && !isLoading) {
      router.push("/dashboard");
    }
  }, [isAuthenticated, isLoading, router]);

  return (
    <div className="min-h-screen flex items-center justify-center bg-slate-50 dark:bg-slate-900 p-4">
      <div className="w-full max-w-md">
        <div className="text-center mb-8">
          <h1 className="text-3xl font-bold">Violt Core Lite</h1>
          <p className="text-slate-500 dark:text-slate-400">
            Open-source smart home automation platform
          </p>
        </div>

        <Card>
          <CardHeader>
            <CardTitle>Welcome back</CardTitle>
            <CardDescription>
              Sign in to your account to continue
            </CardDescription>
          </CardHeader>
          <CardContent>
            <UserAuthForm type="login" />
          </CardContent>
          <CardFooter className="flex justify-center">
            <div className="text-center text-sm">
              Don&#39;t have an account?{" "}
              <Link href="/register" className="underline hover:text-primary">
                Sign up
              </Link>
            </div>
          </CardFooter>
        </Card>
      </div>
    </div>
  );
}

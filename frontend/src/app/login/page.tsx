'use client';

import { useAuth } from "@/services/auth";
import { UserAuthForm } from "@/components/auth/user-auth-form";
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card";
import Link from "next/link";
import Image from "next/image";
import { useEffect } from "react";
import { useRouter } from "next/navigation";
import Logo from "@/assets/logos/violt.png"

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
        <div className="text-center mb-8 flex flex-col items-center">
          <Image
            src={Logo}
            alt="Violt Logo"
            priority={true}
            placeholder="empty"
            width={80}
            height={80}
          />
          <h1 className="text-3xl font-bold">Violt Core</h1>
          <p className="text-slate-500 dark:text-slate-400">
            Smart home automation platform.
          </p>
        </div>

        <Card>
          <CardHeader>
            <CardTitle>Welcome!</CardTitle>
            <CardDescription>
              Sign in to your account to continue.
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
          <div className="text-center text-sm">
            <Link href="/forgot-password" className="underline hover:text-primary">
              Forgot your password?
            </Link>
          </div>
        </Card>
      </div>
    </div>
  );
}

/* eslint-disable @typescript-eslint/no-explicit-any */
'use client';

import { cn } from "@/lib/utils";
import { useAuth } from "@/lib/auth";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { useState } from "react";

interface UserAuthFormProps extends Readonly<React.HTMLAttributes<HTMLDivElement>> {
  readonly type: "login" | "register";
}

export function UserAuthForm({
  className,
  type,
  ...props
}: UserAuthFormProps) {
  const { login } = useAuth();
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [formData, setFormData] = useState({
    name: "",
    username: "",
    email: "",
    password: "",
    confirmPassword: "",
    termsAccepted: false,
  });

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    setFormData((prev) => ({ ...prev, [name]: value }));
  };

  async function onSubmit(event: React.FormEvent) {
    event.preventDefault();
    //setIsLoading(true);

    try {
      // Validate form
      if (type === "register") {
        if (formData.password !== formData.confirmPassword) {
          throw new Error("Passwords do not match");
        }
      }

      if (type === "login") {
        login(formData.username, formData.password);
      } else if (type === "register") {
        // Ensure all required fields are present
        if (!formData.name || !formData.username || !formData.email || !formData.password || typeof formData.termsAccepted === 'undefined') {
          throw new Error("Missing required registration fields");
        }
        register({
          name: formData.name,
          username: formData.username,
          email: formData.email,
          password: formData.password,
          termsAccepted: formData.termsAccepted,
        });
      }

      // Submit to API
      // const endpoint = type === "login" ? "/api/auth/login" : "/api/auth/register";
      // let requestBody: BodyInit;
      // let headers: HeadersInit = {};

      // if (type === "login") {
      //   headers = {
      //     "Content-Type": "application/x-www-form-urlencoded",
      //   };
      //   requestBody = new URLSearchParams({
      //     username: formData.username,
      //     password: formData.password,
      //   });
      // } else { // Register
      //   headers = {
      //     "Content-Type": "application/json",
      //   };
      //   // Ensure all required fields are present
      //   if (!formData.name || !formData.username || !formData.email || !formData.password || typeof formData.termsAccepted === 'undefined') {
      //     throw new Error("Missing required registration fields");
      //   }
      //   requestBody = JSON.stringify({
      //     name: formData.name,
      //     username: formData.username,
      //     email: formData.email,
      //     password: formData.password,
      //     terms_accepted: formData.termsAccepted,
      //   });
      // }

      // console.log(requestBody)

      // const response = await fetch("http://localhost:8000" + endpoint, {
      //   method: "POST",
      //   headers: headers,
      //   body: requestBody,
      // });

      setIsLoading(false);

      // if (!response.ok) {
      //   const error = await response.json();
      //   throw new Error(error.message || "Authentication failed");
      // }

      // // Handle successful authentication
      // console.log(type === 'login' ? 'Login successful:' : 'Registration successful:', await response.json());
      // // Example: Redirect to dashboard after login
      // if (type === 'login') router.push('/dashboard');
    } catch (error: any) {
      setIsLoading(false);
      console.error("Authentication error:", error);
      // TODO: Show error message to the user
    }
  }

  return (
    <div className={cn("grid gap-6", className)} {...props}>
      <form onSubmit={onSubmit}>
        <div className="grid gap-4">
          {type === "register" && (
            <div className="grid gap-2">
              <Label htmlFor="name">Name</Label>
              <Input
                id="name"
                name="name"
                placeholder="John Doe"
                type="text"
                autoCapitalize="none"
                autoComplete="name"
                autoCorrect="off"
                disabled={isLoading}
                value={formData.name}
                onChange={handleChange}
                required
              />
            </div>
          )}
          <div className="grid gap-2">
            <Label htmlFor="username">Username</Label>
            <Input
              id="username"
              name="username"
              placeholder="username"
              type="text"
              autoCapitalize="none"
              autoComplete="username"
              autoCorrect="off"
              disabled={isLoading}
              value={formData.username}
              onChange={handleChange}
              required
            />
          </div>
          {type === "register" && (
            <div className="grid gap-2">
              <Label htmlFor="email">Email</Label>
              <Input
                id="email"
                name="email"
                placeholder="name@example.com"
                type="email"
                autoCapitalize="none"
                autoComplete="email"
                autoCorrect="off"
                disabled={isLoading}
                value={formData.email}
                onChange={handleChange}
                required
              />
            </div>
          )}
          <div className="grid gap-2">
            <Label htmlFor="password">Password</Label>
            <Input
              id="password"
              name="password"
              type="password"
              autoCapitalize="none"
              autoComplete={type === "login" ? "current-password" : "new-password"}
              disabled={isLoading}
              value={formData.password}
              onChange={handleChange}
              required
            />
          </div>
          {type === "register" && (
            <div className="grid gap-2">
              <Label htmlFor="confirmPassword">Confirm Password</Label>
              <Input
                id="confirmPassword"
                name="confirmPassword"
                type="password"
                autoCapitalize="none"
                autoComplete="new-password"
                disabled={isLoading}
                value={formData.confirmPassword}
                onChange={handleChange}
                required
              />
            </div>
          )}
          {type === "register" && (
            <div className="grid gap-2">
              <Label htmlFor="termsAccepted">Terms Accepted</Label>
              <Input
                id="termsAccepted"
                name="termsAccepted"
                type="checkbox"
                disabled={isLoading}
                checked={formData.termsAccepted}
                onChange={(e) => setFormData((prev) => ({ ...prev, termsAccepted: e.target.checked }))}
                required
              />
            </div>
          )}
          <div className="grid gap-2 mt-2">
            <Button disabled={isLoading}>
              {isLoading && (
                <div className="mr-2 h-4 w-4 animate-spin rounded-full border-2 border-slate-200 border-t-slate-800"></div>
              )}
              {type === "login" ? "Sign In" : "Create Account"}
            </Button>
          </div>
        </div>
      </form>
      <div className="relative">
        <div className="absolute inset-0 flex items-center">
          <span className="w-full border-t" />
        </div>
        <div className="relative flex justify-center text-xs uppercase">
          <span className="bg-background px-2 text-muted-foreground">
            Or continue with
          </span>
        </div>
      </div>
      <div className="grid gap-2">
        <Button variant="outline" type="button" disabled={isLoading}>
          {isLoading ? (
            <div className="mr-2 h-4 w-4 animate-spin rounded-full border-2 border-slate-500 border-t-slate-800"></div>
          ) : (
            <svg
              className="mr-2 h-4 w-4"
              xmlns="http://www.w3.org/2000/svg"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="2"
              strokeLinecap="round"
              strokeLinejoin="round"
            >
              <path d="M18 2h-3a5 5 0 0 0-5 5v3H7v4h3v8h4v-8h3l1-4h-4V7a1 1 0 0 1 1-1h3z" />
            </svg>
          )}
          Facebook
        </Button>
        <Button variant="outline" type="button" disabled={isLoading}>
          {isLoading ? (
            <div className="mr-2 h-4 w-4 animate-spin rounded-full border-2 border-slate-500 border-t-slate-800"></div>
          ) : (
            <svg
              className="mr-2 h-4 w-4"
              xmlns="http://www.w3.org/2000/svg"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="2"
              strokeLinecap="round"
              strokeLinejoin="round"
            >
              <path d="M9 19c-5 1.5-5-2.5-7-3m14 6v-3.87a3.37 3.37 0 0 0-.94-2.61c3.14-.35 6.44-1.54 6.44-7A5.44 5.44 0 0 0 20 4.77 5.07 5.07 0 0 0 19.91 1S18.73.65 16 2.48a13.38 13.38 0 0 0-7 0C6.27.65 5.09 1 5.09 1A5.07 5.07 0 0 0 5 4.77a5.44 5.44 0 0 0-1.5 3.78c0 5.42 3.3 6.61 6.44 7A3.37 3.37 0 0 0 9 18.13V22" />
            </svg>
          )}
          GitHub
        </Button>
      </div>
    </div>
  );
}

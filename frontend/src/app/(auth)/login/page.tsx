"use client";

import { useState, useCallback } from "react";
import { useRouter } from "next/navigation";
import { Eye, EyeOff, Loader2, GraduationCap } from "lucide-react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { api, setAccessToken, setRefreshToken, setTenantId } from "@/lib/api";

// Form validation schema
const loginSchema = z.object({
  email: z.string().email("Enter a valid email address"),
  password: z.string().min(1, "Password is required"),
});

type LoginForm = z.infer<typeof loginSchema>;

// Role-based redirect mapping
const roleRedirects: Record<string, string> = {
  student: "/student/dashboard",
  lecturer: "/lecturer/dashboard",
  hod: "/hod/dashboard",
  dean: "/dean/dashboard",
  registrar: "/registrar/dashboard",
  bursar: "/bursar/dashboard",
  vc: "/vc/dashboard",
  ict_admin: "/ict-admin/dashboard",
  alumni: "/alumni/dashboard",
  parent: "/parent/dashboard",
  auditor: "/auditor/dashboard",
  external_examiner: "/external-examiner/dashboard",
};

export default function LoginPage() {
  const router = useRouter();
  const [showPassword, setShowPassword] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Check if 2FA is required
  const [showTwoFactor, setShowTwoFactor] = useState(false);
  const [requires2FA, setRequires2FA] = useState(false);

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<LoginForm>({
    resolver: zodResolver(loginSchema),
  });

  const onSubmit = useCallback(
    async (data: LoginForm) => {
      setIsLoading(true);
      setError(null);

      try {
        const response = await api.post("/auth/login/", data);

        const { access, refresh, user, requires_2fa } = response.data;

        // Check if 2FA is required for this role
        if (requires_2fa) {
          setRequires2FA(true);
          setShowTwoFactor(true);
          return;
        }

        // Save tokens
        setAccessToken(access);
        setRefreshToken(refresh);

        // Set tenant
        if (user.tenant) {
          setTenantId(user.tenant);
        }

        // Redirect based on role
        const redirectPath = roleRedirects[user.role] || "/dashboard";
        router.push(redirectPath);
      } catch (err: any) {
        setError(
          err.response?.data?.detail ||
          err.response?.data?.message ||
          "Invalid email or password"
        );
      } finally {
        setIsLoading(false);
      }
    },
    [router]
  );

  const onTwoFactorSubmit = useCallback(
    async (data: { code: string }) => {
      setIsLoading(true);

      try {
        // Verify 2FA code
        await api.post("/auth/2fa/verify/", data);

        // Redirect to dashboard
        router.push("/dashboard");
      } catch (err: any) {
        setError("Invalid verification code");
      } finally {
        setIsLoading(false);
      }
    },
    [router]
  );

  return (
    <div className="min-h-screen bg-surface-1 flex items-center justify-center p-4">
      <div className="w-full max-w-md">
        {/* University Logo / Branding */}
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center w-16 h-16 bg-brand-primary rounded-xl mb-4">
            <GraduationCap className="w-8 h-8 text-white" />
          </div>
          <h1 className="text-2xl font-display font-bold text-text-primary">
            University MIS
          </h1>
          <p className="text-sm text-text-muted mt-1">
            Nigerian University Management System
          </p>
        </div>

        {/* Login Card */}
        <div className="card">
          <div className="card-header">
            <h2 className="text-lg font-semibold">
              {showTwoFactor ? "Two-Factor Authentication" : "Sign In"}
            </h2>
          </div>

          <div className="card-body">
            {error && (
              <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg">
                <p className="text-sm text-danger">{error}</p>
              </div>
            )}

            {!showTwoFactor ? (
              <form onSubmit={handleSubmit(onSubmit)}>
                {/* Email Field */}
                <div className="mb-4">
                  <label htmlFor="email" className="input-label">
                    Email Address
                  </label>
                  <input
                    id="email"
                    type="email"
                    autoComplete="email"
                    className="input"
                    placeholder="you@university.edu.ng"
                    {...register("email")}
                  />
                  {errors.email && (
                    <p className="mt-1 text-sm text-danger">
                      {errors.email.message}
                    </p>
                  )}
                </div>

                {/* Password Field */}
                <div className="mb-6">
                  <label htmlFor="password" className="input-label">
                    Password
                  </label>
                  <div className="relative">
                    <input
                      id="password"
                      type={showPassword ? "text" : "password"}
                      autoComplete="current-password"
                      className="input pr-12"
                      placeholder="••••••••"
                      {...register("password")}
                    />
                    <button
                      type="button"
                      onClick={() => setShowPassword(!showPassword)}
                      className="absolute right-3 top-1/2 -translate-y-1/2 p-1 text-text-muted hover:text-text-primary"
                    >
                      {showPassword ? (
                        <EyeOff className="w-5 h-5" />
                      ) : (
                        <Eye className="w-5 h-5" />
                      )}
                    </button>
                  </div>
                  {errors.password && (
                    <p className="mt-1 text-sm text-danger">
                      {errors.password.message}
                    </p>
                  )}
                </div>

                {/* Forgot Password Link */}
                <div className="mb-6 text-right">
                  <a
                    href="/forgot-password"
                    className="text-sm text-brand-primary hover:text-brand-primary-light"
                  >
                    Forgot password?
                  </a>
                </div>

                {/* Submit Button */}
                <button
                  type="submit"
                  disabled={isLoading}
                  className="btn btn-primary w-full"
                >
                  {isLoading ? (
                    <Loader2 className="w-5 h-5 animate-spin" />
                  ) : (
                    "Sign In"
                  )}
                </button>
              </form>
            ) : (
              <form onSubmit={handleSubmit(onTwoFactorSubmit)}>
                {/* 2FA Code Field */}
                <div className="mb-4">
                  <label htmlFor="code" className="input-label">
                    Verification Code
                  </label>
                  <input
                    id="code"
                    type="text"
                    inputMode="numeric"
                    pattern="[0-9]*"
                    maxLength={6}
                    autoComplete="one-time-code"
                    className="input text-center text-2xl tracking-[0.5em] font-mono"
                    placeholder="000000"
                    {...register("code", {
                      setValueAs: (v) => v.replace(/\D/g, ""),
                    })}
                  />
                  <p className="mt-2 text-sm text-text-muted">
                    Enter the 6-digit code from your authenticator app
                  </p>
                </div>

                {/* Submit Button */}
                <button
                  type="submit"
                  disabled={isLoading}
                  className="btn btn-primary w-full"
                >
                  {isLoading ? (
                    <Loader2 className="w-5 h-5 animate-spin" />
                  ) : (
                    "Verify"
                  )}
                </button>
              </form>
            )}
          </div>
        </div>

        {/* Footer */}
        <p className="text-center text-sm text-text-muted mt-6">
          NDPA 2023 Compliant • Secure Login
        </p>
      </div>
    </div>
  );
}
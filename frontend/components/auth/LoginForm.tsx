"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { FormEvent, useState } from "react";
import { useAuth } from "@/hooks/useAuth";
import { Button } from "@/components/ui/Button";
import { ErrorState } from "@/components/ui/State";

export function LoginForm() {
  const router = useRouter();
  const { login } = useAuth();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(null);
    setIsSubmitting(true);

    try {
      await login({ email, password });
      router.replace("/dashboard");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to log in.");
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <form className="mx-auto max-w-md rounded-md border border-slate-200 bg-white p-6 shadow-sm" onSubmit={handleSubmit}>
      <div className="space-y-1">
        <h1 className="text-2xl font-semibold tracking-tight">Login</h1>
        <p className="text-sm text-slate-600">Continue to your ApplyPilot workspace.</p>
      </div>
      <label className="mt-5 block space-y-1 text-sm font-medium text-slate-700">
        <span>Email</span>
        <input
          className="w-full rounded-md border border-slate-300 px-3 py-2 outline-none focus:border-slate-950"
          type="email"
          value={email}
          onChange={(event) => setEmail(event.target.value)}
          required
        />
      </label>
      <label className="mt-4 block space-y-1 text-sm font-medium text-slate-700">
        <span>Password</span>
        <input
          className="w-full rounded-md border border-slate-300 px-3 py-2 outline-none focus:border-slate-950"
          type="password"
          value={password}
          onChange={(event) => setPassword(event.target.value)}
          required
        />
      </label>
      {error ? <div className="mt-4"><ErrorState message={error} /></div> : null}
      <Button className="mt-5 w-full" type="submit" disabled={isSubmitting}>
        {isSubmitting ? "Logging in..." : "Login"}
      </Button>
      <p className="mt-4 text-sm text-slate-600">
        New here?{" "}
        <Link className="font-medium text-slate-950 underline" href="/register">
          Create an account
        </Link>
      </p>
    </form>
  );
}

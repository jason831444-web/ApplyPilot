"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { FormEvent, useState } from "react";
import { useAuth } from "@/hooks/useAuth";

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
    <form className="max-w-md space-y-5" onSubmit={handleSubmit}>
      <div className="space-y-1">
        <h1 className="text-2xl font-semibold">Login</h1>
        <p className="text-sm text-slate-600">Continue to your ApplyPilot workspace.</p>
      </div>
      <label className="block space-y-1 text-sm font-medium text-slate-700">
        <span>Email</span>
        <input
          className="w-full rounded-md border border-slate-300 px-3 py-2 outline-none focus:border-slate-950"
          type="email"
          value={email}
          onChange={(event) => setEmail(event.target.value)}
          required
        />
      </label>
      <label className="block space-y-1 text-sm font-medium text-slate-700">
        <span>Password</span>
        <input
          className="w-full rounded-md border border-slate-300 px-3 py-2 outline-none focus:border-slate-950"
          type="password"
          value={password}
          onChange={(event) => setPassword(event.target.value)}
          required
        />
      </label>
      {error ? <p className="rounded-md bg-red-50 px-3 py-2 text-sm text-red-700">{error}</p> : null}
      <button
        className="w-full rounded-md bg-slate-950 px-4 py-2 text-sm font-medium text-white disabled:cursor-not-allowed disabled:bg-slate-400"
        type="submit"
        disabled={isSubmitting}
      >
        {isSubmitting ? "Logging in..." : "Login"}
      </button>
      <p className="text-sm text-slate-600">
        New here?{" "}
        <Link className="font-medium text-slate-950 underline" href="/register">
          Create an account
        </Link>
      </p>
    </form>
  );
}

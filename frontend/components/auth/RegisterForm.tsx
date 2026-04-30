"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { FormEvent, useState } from "react";
import { useAuth } from "@/hooks/useAuth";

export function RegisterForm() {
  const router = useRouter();
  const { register } = useAuth();
  const [fullName, setFullName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(null);
    setIsSubmitting(true);

    try {
      await register({ full_name: fullName, email, password });
      router.replace("/dashboard");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to create account.");
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <form className="max-w-md space-y-5" onSubmit={handleSubmit}>
      <div className="space-y-1">
        <h1 className="text-2xl font-semibold">Register</h1>
        <p className="text-sm text-slate-600">Create your ApplyPilot account.</p>
      </div>
      <label className="block space-y-1 text-sm font-medium text-slate-700">
        <span>Full name</span>
        <input
          className="w-full rounded-md border border-slate-300 px-3 py-2 outline-none focus:border-slate-950"
          value={fullName}
          onChange={(event) => setFullName(event.target.value)}
          required
        />
      </label>
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
          minLength={8}
        />
      </label>
      {error ? <p className="rounded-md bg-red-50 px-3 py-2 text-sm text-red-700">{error}</p> : null}
      <button
        className="w-full rounded-md bg-slate-950 px-4 py-2 text-sm font-medium text-white disabled:cursor-not-allowed disabled:bg-slate-400"
        type="submit"
        disabled={isSubmitting}
      >
        {isSubmitting ? "Creating account..." : "Create account"}
      </button>
      <p className="text-sm text-slate-600">
        Already have an account?{" "}
        <Link className="font-medium text-slate-950 underline" href="/login">
          Login
        </Link>
      </p>
    </form>
  );
}

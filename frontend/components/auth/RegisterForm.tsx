"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { FormEvent, useState } from "react";
import { useAuth } from "@/hooks/useAuth";
import { Button } from "@/components/ui/Button";
import { ErrorState } from "@/components/ui/State";

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
    <form className="mx-auto max-w-md rounded-md border border-slate-200 bg-white p-6 shadow-sm" onSubmit={handleSubmit}>
      <div className="space-y-1">
        <h1 className="text-2xl font-semibold tracking-tight">Register</h1>
        <p className="text-sm text-slate-600">Create your job-fit decision workspace.</p>
      </div>
      <label className="mt-5 block space-y-1 text-sm font-medium text-slate-700">
        <span>Full name</span>
        <input
          className="w-full rounded-md border border-slate-300 px-3 py-2 outline-none focus:border-slate-950"
          value={fullName}
          onChange={(event) => setFullName(event.target.value)}
          maxLength={120}
          required
        />
      </label>
      <label className="mt-4 block space-y-1 text-sm font-medium text-slate-700">
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
          minLength={8}
          maxLength={128}
        />
      </label>
      {error ? <div className="mt-4"><ErrorState message={error} /></div> : null}
      <Button className="mt-5 w-full" type="submit" disabled={isSubmitting}>
        {isSubmitting ? "Creating account..." : "Create account"}
      </Button>
      <p className="mt-4 text-sm text-slate-600">
        Already have an account?{" "}
        <Link className="font-medium text-slate-950 underline" href="/login">
          Login
        </Link>
      </p>
    </form>
  );
}

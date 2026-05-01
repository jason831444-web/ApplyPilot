"use client";

import { useRouter } from "next/navigation";
import { useEffect } from "react";
import { useAuth } from "@/hooks/useAuth";
import { ButtonLink } from "@/components/ui/Button";

export function HomeLanding() {
  const router = useRouter();
  const { isAuthenticated, isLoading } = useAuth();

  useEffect(() => {
    if (!isLoading && isAuthenticated) {
      router.replace("/dashboard");
    }
  }, [isAuthenticated, isLoading, router]);

  return (
    <section className="grid min-h-[70vh] items-center gap-10 lg:grid-cols-[minmax(0,1fr)_420px]">
      <div>
        <p className="text-sm font-semibold uppercase tracking-wide text-slate-500">For new-grad software engineers</p>
        <h1 className="mt-3 max-w-3xl text-4xl font-semibold tracking-tight text-slate-950 sm:text-5xl">
          Decide which jobs deserve your application time.
        </h1>
        <p className="mt-5 max-w-2xl text-base leading-7 text-slate-600">
          ApplyPilot turns a pasted job description into a clear Apply, Caution, Maybe, or Skip recommendation using
          deterministic evidence from your profile, skills, new-grad fit, and work authorization risk.
        </p>
        <div className="mt-7 flex flex-wrap gap-3">
          <ButtonLink href="/register">Create Account</ButtonLink>
          <ButtonLink href="/login" variant="secondary">
            Login
          </ButtonLink>
        </div>
      </div>
      <div className="rounded-md border border-slate-200 bg-white p-5 shadow-sm">
        <h2 className="text-base font-semibold text-slate-950">MVP workflow</h2>
        <ol className="mt-4 space-y-3 text-sm text-slate-700">
          <li className="rounded-md bg-slate-50 p-3">1. Complete your resume profile and target roles.</li>
          <li className="rounded-md bg-slate-50 p-3">2. Paste a job description and run analysis.</li>
          <li className="rounded-md bg-slate-50 p-3">3. Review scores, evidence, missing skills, and risk.</li>
          <li className="rounded-md bg-slate-50 p-3">4. Track the application pipeline from saved to offer.</li>
        </ol>
      </div>
    </section>
  );
}

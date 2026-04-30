"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { useAuth } from "@/hooks/useAuth";
import { apiRequest } from "@/lib/api";
import { formatTitle } from "@/lib/format";
import type { Job } from "@/lib/types";

function formatDate(value: string): string {
  return new Intl.DateTimeFormat("en", { dateStyle: "medium", timeStyle: "short" }).format(new Date(value));
}

export function JobDetailView({ jobId }: { jobId: string }) {
  const { token } = useAuth();
  const [job, setJob] = useState<Job | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!token) {
      return;
    }

    let isMounted = true;

    async function loadJob() {
      setIsLoading(true);
      setError(null);
      try {
        const data = await apiRequest<Job>(`/api/jobs/${jobId}`, { token });
        if (isMounted) {
          setJob(data);
        }
      } catch (err) {
        if (isMounted) {
          setError(err instanceof Error ? err.message : "Unable to load job.");
        }
      } finally {
        if (isMounted) {
          setIsLoading(false);
        }
      }
    }

    void loadJob();

    return () => {
      isMounted = false;
    };
  }, [jobId, token]);

  if (isLoading) {
    return <p className="text-sm text-slate-600">Loading job...</p>;
  }

  if (error) {
    return <p className="rounded-md bg-red-50 px-3 py-2 text-sm text-red-700">{error}</p>;
  }

  if (!job) {
    return <p className="text-sm text-slate-600">Job not found.</p>;
  }

  return (
    <section className="space-y-6">
      <div className="space-y-2">
        <Link className="text-sm font-medium text-slate-600 underline" href="/jobs">
          Back to jobs
        </Link>
        <div>
          <h1 className="text-2xl font-semibold">{job.job_title}</h1>
          <p className="text-slate-600">
            {job.company_name} {job.location ? `- ${job.location}` : ""}
          </p>
        </div>
      </div>

      <div className="grid gap-4 md:grid-cols-3">
        <div className="rounded-md border border-slate-200 bg-white p-4">
          <p className="text-xs font-medium uppercase tracking-wide text-slate-500">Created</p>
          <p className="mt-1 text-sm text-slate-900">{formatDate(job.created_at)}</p>
        </div>
        <div className="rounded-md border border-slate-200 bg-white p-4">
          <p className="text-xs font-medium uppercase tracking-wide text-slate-500">Source</p>
          <p className="mt-1 text-sm text-slate-900">{formatTitle(job.source_type)}</p>
        </div>
        <div className="rounded-md border border-slate-200 bg-white p-4">
          <p className="text-xs font-medium uppercase tracking-wide text-slate-500">Application status</p>
          <p className="mt-1 text-sm text-slate-900">
            {job.application ? formatTitle(job.application.status) : "No application record"}
          </p>
        </div>
      </div>

      {job.source_url ? (
        <p className="text-sm text-slate-600">
          Source URL:{" "}
          <a className="font-medium text-slate-950 underline" href={job.source_url} rel="noreferrer" target="_blank">
            {job.source_url}
          </a>
        </p>
      ) : null}

      <div className="rounded-md border border-slate-200 bg-white p-5">
        <h2 className="text-lg font-semibold">Analysis</h2>
        <p className="mt-2 text-sm text-slate-600">Analysis will appear here after the decision engine is implemented.</p>
      </div>

      <div className="rounded-md border border-slate-200 bg-white p-5">
        <h2 className="text-lg font-semibold">Job Description</h2>
        <pre className="mt-4 whitespace-pre-wrap break-words text-sm leading-6 text-slate-700">{job.job_description}</pre>
      </div>
    </section>
  );
}

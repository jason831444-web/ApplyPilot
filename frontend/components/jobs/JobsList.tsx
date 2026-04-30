"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { useAuth } from "@/hooks/useAuth";
import { apiRequest } from "@/lib/api";
import type { Job } from "@/lib/types";

function formatDate(value: string): string {
  return new Intl.DateTimeFormat("en", { dateStyle: "medium" }).format(new Date(value));
}

export function JobsList() {
  const { token } = useAuth();
  const [jobs, setJobs] = useState<Job[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!token) {
      return;
    }

    let isMounted = true;

    async function loadJobs() {
      setIsLoading(true);
      setError(null);
      try {
        const data = await apiRequest<Job[]>("/api/jobs", { token });
        if (isMounted) {
          setJobs(data);
        }
      } catch (err) {
        if (isMounted) {
          setError(err instanceof Error ? err.message : "Unable to load jobs.");
        }
      } finally {
        if (isMounted) {
          setIsLoading(false);
        }
      }
    }

    void loadJobs();

    return () => {
      isMounted = false;
    };
  }, [token]);

  if (isLoading) {
    return <p className="text-sm text-slate-600">Loading jobs...</p>;
  }

  return (
    <section className="space-y-5">
      <div className="flex items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-semibold">Jobs</h1>
          <p className="text-sm text-slate-600">Saved postings ready for analysis and tracking.</p>
        </div>
        <Link className="rounded-md bg-slate-950 px-4 py-2 text-sm font-medium text-white" href="/jobs/new">
          New Job
        </Link>
      </div>

      {error ? <p className="rounded-md bg-red-50 px-3 py-2 text-sm text-red-700">{error}</p> : null}

      {jobs.length === 0 ? (
        <div className="rounded-md border border-dashed border-slate-300 bg-white px-4 py-8">
          <p className="text-sm text-slate-600">No jobs yet. Paste a job description to start your decision workflow.</p>
        </div>
      ) : (
        <div className="overflow-hidden rounded-md border border-slate-200 bg-white">
          <table className="w-full border-collapse text-left text-sm">
            <thead className="bg-slate-50 text-slate-600">
              <tr>
                <th className="px-4 py-3 font-medium">Company</th>
                <th className="px-4 py-3 font-medium">Title</th>
                <th className="px-4 py-3 font-medium">Location</th>
                <th className="px-4 py-3 font-medium">Created</th>
                <th className="px-4 py-3 font-medium">Source</th>
              </tr>
            </thead>
            <tbody>
              {jobs.map((job) => (
                <tr key={job.id} className="border-t border-slate-200 hover:bg-slate-50">
                  <td className="px-4 py-3 font-medium text-slate-950">
                    <Link href={`/jobs/${job.id}`}>{job.company_name}</Link>
                  </td>
                  <td className="px-4 py-3">
                    <Link href={`/jobs/${job.id}`}>{job.job_title}</Link>
                  </td>
                  <td className="px-4 py-3 text-slate-600">{job.location || "Not specified"}</td>
                  <td className="px-4 py-3 text-slate-600">{formatDate(job.created_at)}</td>
                  <td className="px-4 py-3 text-slate-600">{job.source_type}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </section>
  );
}

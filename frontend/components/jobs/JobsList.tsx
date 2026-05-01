"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { useAuth } from "@/hooks/useAuth";
import { apiRequest } from "@/lib/api";
import { formatTitle } from "@/lib/format";
import type { Job } from "@/lib/types";
import { ButtonLink } from "@/components/ui/Button";
import { ScoreBadge } from "@/components/ui/Badge";
import { EmptyState, ErrorState, LoadingState } from "@/components/ui/State";
import { PageHeader } from "@/components/ui/PageHeader";
import { RecommendationBadge } from "./RecommendationBadge";

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
    return <LoadingState label="Loading jobs..." />;
  }

  return (
    <section className="space-y-5">
      <PageHeader
        title="Jobs"
        description="Saved postings with decision-engine recommendations and application status."
        action={<ButtonLink href="/jobs/new">Add Job</ButtonLink>}
      />

      {error ? <ErrorState message={error} /> : null}

      {jobs.length === 0 ? (
        <EmptyState
          title="No jobs yet"
          description="Paste a job description to start your decision workflow."
          actionHref="/jobs/new"
          actionLabel="Analyze Job"
        />
      ) : (
        <div className="overflow-x-auto rounded-md border border-slate-200 bg-white">
          <table className="w-full min-w-[880px] border-collapse text-left text-sm">
            <thead className="bg-slate-50 text-slate-600">
              <tr>
                <th className="px-4 py-3 font-medium">Company</th>
                <th className="px-4 py-3 font-medium">Title</th>
                <th className="px-4 py-3 font-medium">Location</th>
                <th className="px-4 py-3 font-medium">Decision</th>
                <th className="px-4 py-3 font-medium">Score</th>
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
                  <td className="px-4 py-3">
                    {job.analysis ? (
                      <div className="flex flex-wrap gap-2">
                        <RecommendationBadge type="recommendation" value={job.analysis.recommendation} />
                        <RecommendationBadge type="risk" value={job.analysis.authorization_risk} />
                      </div>
                    ) : (
                      <span className="text-slate-500">Not analyzed</span>
                    )}
                  </td>
                  <td className="px-4 py-3"><ScoreBadge score={job.analysis?.overall_score} /></td>
                  <td className="px-4 py-3 text-slate-600">{formatDate(job.created_at)}</td>
                  <td className="px-4 py-3 text-slate-600">{formatTitle(job.source_type)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </section>
  );
}

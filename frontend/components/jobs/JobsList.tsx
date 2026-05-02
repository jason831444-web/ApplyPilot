"use client";

import Link from "next/link";
import { useCallback, useEffect, useState } from "react";
import { useAuth } from "@/hooks/useAuth";
import { apiRequest, bulkDeleteJobs } from "@/lib/api";
import { formatTitle } from "@/lib/format";
import type { Job } from "@/lib/types";
import { Button, ButtonLink } from "@/components/ui/Button";
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
  const [selectedJobIds, setSelectedJobIds] = useState<number[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isDeleting, setIsDeleting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);

  const loadJobs = useCallback(async () => {
    if (!token) {
      return;
    }

    setIsLoading(true);
    setError(null);
    try {
      const data = await apiRequest<Job[]>("/api/jobs", { token });
      setJobs(data);
      setSelectedJobIds((currentIds) => currentIds.filter((id) => data.some((job) => job.id === id)));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to load jobs.");
    } finally {
      setIsLoading(false);
    }
  }, [token]);

  useEffect(() => {
    void loadJobs();
  }, [loadJobs]);

  const allVisibleSelected = jobs.length > 0 && jobs.every((job) => selectedJobIds.includes(job.id));

  function toggleJobSelection(jobId: number) {
    setSelectedJobIds((currentIds) =>
      currentIds.includes(jobId) ? currentIds.filter((id) => id !== jobId) : [...currentIds, jobId],
    );
    setSuccessMessage(null);
  }

  function toggleAllVisibleJobs() {
    setSuccessMessage(null);
    setSelectedJobIds(allVisibleSelected ? [] : jobs.map((job) => job.id));
  }

  async function handleBulkDelete() {
    if (!token || selectedJobIds.length === 0) {
      return;
    }

    const confirmed = window.confirm(
      "Delete selected jobs? This will also remove related applications and analyses.",
    );
    if (!confirmed) {
      return;
    }

    setIsDeleting(true);
    setError(null);
    setSuccessMessage(null);
    try {
      const result = await bulkDeleteJobs(selectedJobIds, token);
      setSuccessMessage(`Deleted ${result.deleted_count} selected job${result.deleted_count === 1 ? "" : "s"}.`);
      setSelectedJobIds([]);
      await loadJobs();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to delete selected jobs.");
    } finally {
      setIsDeleting(false);
    }
  }

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
      {successMessage ? (
        <p className="rounded-md bg-emerald-50 px-3 py-2 text-sm text-emerald-800">{successMessage}</p>
      ) : null}

      {jobs.length === 0 ? (
        <EmptyState
          title="No jobs yet"
          description="Paste a job description to start your decision workflow."
          actionHref="/jobs/new"
          actionLabel="Analyze Job"
        />
      ) : (
        <div className="space-y-3">
          <div className="flex flex-wrap items-center justify-between gap-3 rounded-md border border-slate-200 bg-white px-4 py-3">
            <p className="text-sm text-slate-600">
              {selectedJobIds.length} selected
            </p>
            <Button
              disabled={selectedJobIds.length === 0 || isDeleting}
              onClick={handleBulkDelete}
              variant="secondary"
            >
              {isDeleting ? "Deleting..." : "Delete selected"}
            </Button>
          </div>
          <div className="overflow-x-auto rounded-md border border-slate-200 bg-white">
          <table className="w-full min-w-[880px] border-collapse text-left text-sm">
            <thead className="bg-slate-50 text-slate-600">
              <tr>
                <th className="w-12 px-4 py-3 font-medium">
                  <input
                    aria-label="Select all visible jobs"
                    checked={allVisibleSelected}
                    className="h-4 w-4 rounded border-slate-300"
                    onChange={toggleAllVisibleJobs}
                    type="checkbox"
                  />
                </th>
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
                  <td className="px-4 py-3">
                    <input
                      aria-label={`Select ${job.company_name} ${job.job_title}`}
                      checked={selectedJobIds.includes(job.id)}
                      className="h-4 w-4 rounded border-slate-300"
                      onChange={() => toggleJobSelection(job.id)}
                      type="checkbox"
                    />
                  </td>
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
        </div>
      )}
    </section>
  );
}

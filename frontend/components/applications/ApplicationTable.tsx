"use client";

import Link from "next/link";
import { useCallback, useEffect, useMemo, useState } from "react";
import { RecommendationBadge } from "@/components/jobs/RecommendationBadge";
import { useAuth } from "@/hooks/useAuth";
import { apiRequest, bulkDeleteApplications, exportApplicationsCsv } from "@/lib/api";
import { formatTitle } from "@/lib/format";
import type { ApplicationStatus, ApplicationWithJob } from "@/lib/types";
import { Button } from "@/components/ui/Button";
import { EmptyState, ErrorState, LoadingState } from "@/components/ui/State";
import { PageHeader } from "@/components/ui/PageHeader";
import { ScoreBadge } from "@/components/ui/Badge";
import { APPLICATION_STATUSES, ApplicationStatusBadge } from "./ApplicationStatusSelect";

function formatDate(value: string | null): string {
  if (!value) {
    return "Not set";
  }
  return new Intl.DateTimeFormat("en", { dateStyle: "medium" }).format(new Date(`${value}T00:00:00`));
}

function isUpcoming(value: string | null): boolean {
  if (!value) {
    return false;
  }
  const today = new Date();
  today.setHours(0, 0, 0, 0);
  const target = new Date(`${value}T00:00:00`);
  const days = (target.getTime() - today.getTime()) / (1000 * 60 * 60 * 24);
  return days >= 0 && days <= 7;
}

export function ApplicationTable() {
  const { token } = useAuth();
  const [applications, setApplications] = useState<ApplicationWithJob[]>([]);
  const [selectedApplicationIds, setSelectedApplicationIds] = useState<number[]>([]);
  const [statusFilter, setStatusFilter] = useState<ApplicationStatus | "all">("all");
  const [isLoading, setIsLoading] = useState(true);
  const [isDeleting, setIsDeleting] = useState(false);
  const [isExporting, setIsExporting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);

  const loadApplications = useCallback(async () => {
    if (!token) {
      return;
    }

    setIsLoading(true);
    setError(null);
    try {
      const data = await apiRequest<ApplicationWithJob[]>("/api/applications", { token });
      setApplications(data);
      setSelectedApplicationIds((currentIds) =>
        currentIds.filter((id) => data.some((application) => application.id === id)),
      );
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to load applications.");
    } finally {
      setIsLoading(false);
    }
  }, [token]);

  useEffect(() => {
    void loadApplications();
  }, [loadApplications]);

  const filteredApplications = useMemo(
    () =>
      statusFilter === "all"
        ? applications
        : applications.filter((application) => application.status === statusFilter),
    [applications, statusFilter],
  );

  useEffect(() => {
    setSelectedApplicationIds((currentIds) =>
      currentIds.filter((id) => filteredApplications.some((application) => application.id === id)),
    );
  }, [filteredApplications]);

  const allVisibleSelected =
    filteredApplications.length > 0 &&
    filteredApplications.every((application) => selectedApplicationIds.includes(application.id));

  function toggleApplicationSelection(applicationId: number) {
    setSelectedApplicationIds((currentIds) =>
      currentIds.includes(applicationId)
        ? currentIds.filter((id) => id !== applicationId)
        : [...currentIds, applicationId],
    );
    setSuccessMessage(null);
  }

  function toggleAllVisibleApplications() {
    setSuccessMessage(null);
    setSelectedApplicationIds(allVisibleSelected ? [] : filteredApplications.map((application) => application.id));
  }

  async function handleBulkDelete() {
    if (!token || selectedApplicationIds.length === 0) {
      return;
    }

    const confirmed = window.confirm("Delete selected applications?");
    if (!confirmed) {
      return;
    }

    setIsDeleting(true);
    setError(null);
    setSuccessMessage(null);
    try {
      const result = await bulkDeleteApplications(selectedApplicationIds, token);
      setSuccessMessage(
        `Deleted ${result.deleted_count} selected application${result.deleted_count === 1 ? "" : "s"}.`,
      );
      setSelectedApplicationIds([]);
      await loadApplications();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to delete selected applications.");
    } finally {
      setIsDeleting(false);
    }
  }

  async function handleExportCsv() {
    if (!token) {
      return;
    }

    setIsExporting(true);
    setError(null);
    try {
      const blob = await exportApplicationsCsv(token);
      const url = URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = url;
      link.download = "applypilot_applications.csv";
      document.body.appendChild(link);
      link.click();
      link.remove();
      URL.revokeObjectURL(url);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to export applications.");
    } finally {
      setIsExporting(false);
    }
  }

  if (isLoading) {
    return <LoadingState label="Loading applications..." />;
  }

  return (
    <section className="space-y-5">
      <div className="flex flex-wrap items-end justify-between gap-4">
        <PageHeader
          title="Applications"
          description="Your active job-search pipeline across saved and applied roles."
          action={
            <Button disabled={isExporting} onClick={handleExportCsv} type="button" variant="secondary">
              {isExporting ? "Exporting..." : "Export CSV"}
            </Button>
          }
        />
        <label className="block space-y-1 text-sm font-medium text-slate-700">
          <span>Status filter</span>
          <select
            className="rounded-md border border-slate-300 px-3 py-2 text-sm outline-none focus:border-slate-950"
            value={statusFilter}
            onChange={(event) => setStatusFilter(event.target.value as ApplicationStatus | "all")}
          >
            <option value="all">All statuses</option>
            {APPLICATION_STATUSES.map((status) => (
              <option key={status} value={status}>
                {formatTitle(status)}
              </option>
            ))}
          </select>
        </label>
      </div>

      {error ? <ErrorState message={error} /> : null}
      {successMessage ? (
        <p className="rounded-md bg-emerald-50 px-3 py-2 text-sm text-emerald-800">{successMessage}</p>
      ) : null}

      {filteredApplications.length === 0 ? (
        <EmptyState
          title="No applications found"
          description="Analyze or save a job to start tracking it here."
          actionHref="/jobs/new"
          actionLabel="Analyze Job"
        />
      ) : (
        <div className="space-y-3">
          <div className="flex flex-wrap items-center justify-between gap-3 rounded-md border border-slate-200 bg-white px-4 py-3">
            <p className="text-sm text-slate-600">
              {selectedApplicationIds.length} selected
            </p>
            <Button
              disabled={selectedApplicationIds.length === 0 || isDeleting}
              onClick={handleBulkDelete}
              variant="secondary"
            >
              {isDeleting ? "Deleting..." : "Delete selected"}
            </Button>
          </div>
          <div className="overflow-x-auto rounded-md border border-slate-200 bg-white">
          <table className="w-full min-w-[960px] border-collapse text-left text-sm">
            <thead className="bg-slate-50 text-slate-600">
              <tr>
                <th className="w-12 px-4 py-3 font-medium">
                  <input
                    aria-label="Select all visible applications"
                    checked={allVisibleSelected}
                    className="h-4 w-4 rounded border-slate-300"
                    onChange={toggleAllVisibleApplications}
                    type="checkbox"
                  />
                </th>
                <th className="px-4 py-3 font-medium">Company</th>
                <th className="px-4 py-3 font-medium">Role</th>
                <th className="px-4 py-3 font-medium">Location</th>
                <th className="px-4 py-3 font-medium">Status</th>
                <th className="px-4 py-3 font-medium">Applied</th>
                <th className="px-4 py-3 font-medium">Next action</th>
                <th className="px-4 py-3 font-medium">Decision</th>
                <th className="px-4 py-3 font-medium">Score</th>
              </tr>
            </thead>
            <tbody>
              {filteredApplications.map((application) => (
                <tr key={application.id} className="border-t border-slate-200 hover:bg-slate-50">
                  <td className="px-4 py-3">
                    <input
                      aria-label={`Select ${application.job.company_name} ${application.job.job_title}`}
                      checked={selectedApplicationIds.includes(application.id)}
                      className="h-4 w-4 rounded border-slate-300"
                      onChange={() => toggleApplicationSelection(application.id)}
                      type="checkbox"
                    />
                  </td>
                  <td className="px-4 py-3 font-medium text-slate-950">
                    <Link href={`/jobs/${application.job.id}`}>{application.job.company_name}</Link>
                  </td>
                  <td className="px-4 py-3">
                    <Link href={`/jobs/${application.job.id}`}>{application.job.job_title}</Link>
                  </td>
                  <td className="px-4 py-3 text-slate-600">{application.job.location || "Not specified"}</td>
                  <td className="px-4 py-3">
                    <ApplicationStatusBadge status={application.status} />
                  </td>
                  <td className="px-4 py-3 text-slate-600">{formatDate(application.applied_date)}</td>
                  <td className="px-4 py-3">
                    <p className="text-slate-900">{application.next_action || "None"}</p>
                    <p className={isUpcoming(application.next_action_date) ? "mt-1 font-medium text-amber-700" : "mt-1 text-slate-500"}>
                      {formatDate(application.next_action_date)}
                    </p>
                  </td>
                  <td className="px-4 py-3">
                    {application.analysis ? (
                      <div className="flex flex-wrap gap-2">
                        <RecommendationBadge type="recommendation" value={application.analysis.recommendation} />
                        <RecommendationBadge type="risk" value={application.analysis.authorization_risk} />
                      </div>
                    ) : (
                      <span className="text-slate-500">Not analyzed</span>
                    )}
                  </td>
                  <td className="px-4 py-3"><ScoreBadge score={application.analysis?.overall_score} /></td>
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

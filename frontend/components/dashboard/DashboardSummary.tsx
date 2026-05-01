"use client";

import { useEffect, useState } from "react";
import { useAuth } from "@/hooks/useAuth";
import { apiRequest } from "@/lib/api";
import type { DashboardSummary as DashboardSummaryType } from "@/lib/types";
import { ActionList, BestOpportunities, CautionReasons, EmptyDashboard, UpcomingFollowups } from "./InsightList";
import { MissingSkillsChart } from "./MissingSkillsChart";
import { RecommendationChart } from "./RecommendationChart";
import { StatusChart } from "./StatusChart";

function KpiCard({ label, value }: { label: string; value: string | number }) {
  return (
    <div className="rounded-md border border-slate-200 bg-white p-4">
      <p className="text-xs font-medium uppercase tracking-wide text-slate-500">{label}</p>
      <p className="mt-2 text-2xl font-semibold text-slate-950">{value}</p>
    </div>
  );
}

export function DashboardSummary() {
  const { token } = useAuth();
  const [summary, setSummary] = useState<DashboardSummaryType | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!token) {
      return;
    }

    let isMounted = true;

    async function loadSummary() {
      setIsLoading(true);
      setError(null);
      try {
        const data = await apiRequest<DashboardSummaryType>("/api/dashboard/summary", { token });
        if (isMounted) {
          setSummary(data);
        }
      } catch (err) {
        if (isMounted) {
          setError(err instanceof Error ? err.message : "Unable to load dashboard.");
        }
      } finally {
        if (isMounted) {
          setIsLoading(false);
        }
      }
    }

    void loadSummary();

    return () => {
      isMounted = false;
    };
  }, [token]);

  if (isLoading) {
    return <p className="text-sm text-slate-600">Loading dashboard...</p>;
  }

  if (error) {
    return <p className="rounded-md bg-red-50 px-3 py-2 text-sm text-red-700">{error}</p>;
  }

  if (!summary) {
    return <EmptyDashboard />;
  }

  const isEmpty = summary.total_jobs === 0 && summary.total_applications === 0;

  return (
    <section className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold">Dashboard</h1>
        <p className="text-sm text-slate-600">Pipeline health, job-fit signals, and the next moves worth making.</p>
      </div>

      {isEmpty ? <EmptyDashboard /> : null}

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <KpiCard label="Total jobs" value={summary.total_jobs} />
        <KpiCard label="Applications" value={summary.total_applications} />
        <KpiCard label="Saved" value={summary.saved_count} />
        <KpiCard label="Applied" value={summary.applied_count} />
        <KpiCard label="Interviews" value={summary.interview_count} />
        <KpiCard label="Rejections" value={summary.rejected_count} />
        <KpiCard label="Offers" value={summary.offer_count} />
        <KpiCard label="Average match" value={summary.average_match_score === null ? "N/A" : `${summary.average_match_score}`} />
      </div>

      <div className="grid gap-4 xl:grid-cols-2">
        <StatusChart title="Applications by Status" data={summary.applications_by_status} />
        <RecommendationChart title="Recommendation Distribution" data={summary.recommendation_distribution} />
        <RecommendationChart title="Authorization Risk" data={summary.authorization_risk_distribution} />
        <RecommendationChart title="New-Grad Fit" data={summary.new_grad_fit_distribution} />
      </div>

      <MissingSkillsChart data={summary.top_missing_skills} />

      <div className="grid gap-4 xl:grid-cols-2">
        <ActionList actions={summary.next_recommended_actions} />
        <UpcomingFollowups followups={summary.upcoming_followups} />
        <BestOpportunities opportunities={summary.best_opportunities} />
        <CautionReasons reasons={summary.caution_reasons} />
      </div>
    </section>
  );
}

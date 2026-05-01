import Link from "next/link";
import { ApplicationStatusBadge } from "@/components/applications/ApplicationStatusSelect";
import { RecommendationBadge } from "@/components/jobs/RecommendationBadge";
import { formatTitle } from "@/lib/format";
import type { BestOpportunity, CautionReason, UpcomingFollowup } from "@/lib/types";

function formatDate(value: string): string {
  return new Intl.DateTimeFormat("en", { dateStyle: "medium" }).format(new Date(`${value}T00:00:00`));
}

export function ActionList({ actions }: { actions: string[] }) {
  return (
    <section className="rounded-md border border-slate-200 bg-white p-5">
      <h2 className="text-base font-semibold">Next Recommended Actions</h2>
      <ul className="mt-3 list-disc space-y-2 pl-5 text-sm leading-6 text-slate-700">
        {actions.map((action) => (
          <li key={action}>{action}</li>
        ))}
      </ul>
    </section>
  );
}

export function UpcomingFollowups({ followups }: { followups: UpcomingFollowup[] }) {
  return (
    <section className="rounded-md border border-slate-200 bg-white p-5">
      <h2 className="text-base font-semibold">Upcoming Follow-Ups</h2>
      {followups.length === 0 ? (
        <p className="mt-3 text-sm text-slate-500">No dated follow-ups yet.</p>
      ) : (
        <ul className="mt-3 space-y-3">
          {followups.map((followup) => (
            <li key={followup.application_id} className="rounded-md border border-slate-200 bg-slate-50 p-3">
              <div className="flex flex-wrap items-start justify-between gap-2">
                <div>
                  <Link className="font-medium text-slate-950 underline" href={`/jobs/${followup.job_id}`}>
                    {followup.company_name}
                  </Link>
                  <p className="text-sm text-slate-600">{followup.job_title}</p>
                </div>
                <ApplicationStatusBadge status={followup.status} />
              </div>
              <p className="mt-2 text-sm text-slate-700">{followup.next_action || "Follow up"}</p>
              <p className="mt-1 text-sm font-medium text-amber-700">{formatDate(followup.next_action_date)}</p>
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}

export function BestOpportunities({ opportunities }: { opportunities: BestOpportunity[] }) {
  return (
    <section className="rounded-md border border-slate-200 bg-white p-5">
      <h2 className="text-base font-semibold">Best Opportunities</h2>
      {opportunities.length === 0 ? (
        <p className="mt-3 text-sm text-slate-500">No high-fit active opportunities yet.</p>
      ) : (
        <ul className="mt-3 space-y-3">
          {opportunities.map((opportunity) => (
            <li key={opportunity.job_id} className="rounded-md border border-slate-200 bg-slate-50 p-3">
              <div className="flex flex-wrap items-start justify-between gap-2">
                <div>
                  <Link className="font-medium text-slate-950 underline" href={`/jobs/${opportunity.job_id}`}>
                    {opportunity.company_name}
                  </Link>
                  <p className="text-sm text-slate-600">
                    {opportunity.job_title} {opportunity.location ? `- ${opportunity.location}` : ""}
                  </p>
                </div>
                <p className="text-lg font-semibold text-slate-950">{opportunity.overall_score}</p>
              </div>
              <div className="mt-3 flex flex-wrap gap-2">
                <RecommendationBadge type="recommendation" value={opportunity.recommendation} />
                <RecommendationBadge type="risk" value={opportunity.authorization_risk} />
                {opportunity.status ? <ApplicationStatusBadge status={opportunity.status} /> : null}
              </div>
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}

export function CautionReasons({ reasons }: { reasons: CautionReason[] }) {
  return (
    <section className="rounded-md border border-slate-200 bg-white p-5">
      <h2 className="text-base font-semibold">Common Caution Reasons</h2>
      {reasons.length === 0 ? (
        <p className="mt-3 text-sm text-slate-500">No repeated concerns yet.</p>
      ) : (
        <ul className="mt-3 space-y-2 text-sm text-slate-700">
          {reasons.map((reason) => (
            <li key={reason.reason} className="flex justify-between gap-3 rounded-md border border-slate-200 px-3 py-2">
              <span>{reason.reason}</span>
              <span className="font-semibold text-slate-950">{reason.count}</span>
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}

export function EmptyDashboard() {
  return (
    <div className="rounded-md border border-dashed border-slate-300 bg-white px-4 py-8">
      <p className="text-sm text-slate-600">
        Analyze a job or save an application to populate dashboard insights.
      </p>
      <Link className="mt-4 inline-flex rounded-md bg-slate-950 px-4 py-2 text-sm font-medium text-white" href="/jobs/new">
        Analyze Job
      </Link>
    </div>
  );
}

export function DistributionLegend({ label }: { label: string }) {
  return <span className="text-xs font-medium uppercase tracking-wide text-slate-500">{formatTitle(label)}</span>;
}

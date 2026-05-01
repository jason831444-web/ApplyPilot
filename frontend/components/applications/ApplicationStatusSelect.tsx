"use client";

import { formatTitle } from "@/lib/format";
import type { ApplicationStatus } from "@/lib/types";

export const APPLICATION_STATUSES: ApplicationStatus[] = [
  "saved",
  "applied",
  "online_assessment",
  "recruiter_screen",
  "technical_interview",
  "final_interview",
  "offer",
  "rejected",
  "withdrawn",
  "archived",
];

export function statusBadgeClass(status: ApplicationStatus): string {
  if (status === "offer") {
    return "border-emerald-200 bg-emerald-50 text-emerald-800";
  }
  if (["rejected", "withdrawn", "archived"].includes(status)) {
    return "border-slate-200 bg-slate-100 text-slate-700";
  }
  if (["technical_interview", "final_interview", "recruiter_screen"].includes(status)) {
    return "border-sky-200 bg-sky-50 text-sky-800";
  }
  if (status === "online_assessment") {
    return "border-violet-200 bg-violet-50 text-violet-800";
  }
  if (status === "applied") {
    return "border-amber-200 bg-amber-50 text-amber-800";
  }
  return "border-slate-200 bg-white text-slate-700";
}

export function ApplicationStatusBadge({ status }: { status: ApplicationStatus }) {
  return (
    <span className={`inline-flex rounded-md border px-2.5 py-1 text-xs font-semibold ${statusBadgeClass(status)}`}>
      {formatTitle(status)}
    </span>
  );
}

export function ApplicationStatusSelect({
  value,
  onChange,
}: {
  value: ApplicationStatus;
  onChange: (value: ApplicationStatus) => void;
}) {
  return (
    <select
      className="w-full rounded-md border border-slate-300 px-3 py-2 text-sm outline-none focus:border-slate-950"
      value={value}
      onChange={(event) => onChange(event.target.value as ApplicationStatus)}
    >
      {APPLICATION_STATUSES.map((status) => (
        <option key={status} value={status}>
          {formatTitle(status)}
        </option>
      ))}
    </select>
  );
}

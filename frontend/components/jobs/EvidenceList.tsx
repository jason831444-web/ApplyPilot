"use client";

import { useMemo, useState } from "react";
import type { AnalysisEvidence } from "@/lib/types";

type GroupedEvidence = {
  label: string;
  items: AnalysisEvidence[];
};

export function EvidenceList({
  evidence,
  emptyText,
  maxInitialItems = 6,
}: {
  evidence: AnalysisEvidence[];
  emptyText: string;
  maxInitialItems?: number;
}) {
  const [isExpanded, setIsExpanded] = useState(false);
  const groupedEvidence = useMemo(() => groupEvidence(evidence), [evidence]);
  const visibleGroups = useMemo(
    () => limitEvidenceGroups(groupedEvidence, isExpanded ? Number.POSITIVE_INFINITY : maxInitialItems),
    [groupedEvidence, isExpanded, maxInitialItems],
  );
  const totalCount = groupedEvidence.reduce((count, group) => count + group.items.length, 0);

  if (evidence.length === 0) {
    return <p className="text-sm text-slate-500">{emptyText}</p>;
  }

  return (
    <div className="space-y-3">
      {visibleGroups.map((group) => (
        <div key={group.label} className="rounded-md border border-slate-200 bg-slate-50 px-3 py-2">
          <p className="text-sm font-semibold text-slate-900">{group.label}</p>
          <ul className="mt-2 space-y-2">
            {group.items.map((item, index) => (
              <li key={`${item.type}-${item.label}-${index}`} className="text-sm leading-6 text-slate-600">
                {item.text}
              </li>
            ))}
          </ul>
        </div>
      ))}
      {totalCount > maxInitialItems ? (
        <button
          className="text-sm font-medium text-slate-700 underline"
          onClick={() => setIsExpanded((value) => !value)}
          type="button"
        >
          {isExpanded ? "Show less evidence" : `Show ${totalCount - maxInitialItems} more evidence items`}
        </button>
      ) : null}
    </div>
  );
}

function groupEvidence(evidence: AnalysisEvidence[]): GroupedEvidence[] {
  const groups = new Map<string, AnalysisEvidence[]>();
  for (const item of evidence) {
    const key = item.label || item.type || "Evidence";
    groups.set(key, [...(groups.get(key) ?? []), item]);
  }
  return Array.from(groups, ([label, items]) => ({ label, items: items.slice(0, 2) }));
}

function limitEvidenceGroups(groups: GroupedEvidence[], maxItems: number): GroupedEvidence[] {
  const visibleGroups: GroupedEvidence[] = [];
  let count = 0;
  for (const group of groups) {
    if (count >= maxItems) {
      break;
    }
    const remaining = maxItems - count;
    const items = group.items.slice(0, remaining);
    visibleGroups.push({ label: group.label, items });
    count += items.length;
  }
  return visibleGroups;
}

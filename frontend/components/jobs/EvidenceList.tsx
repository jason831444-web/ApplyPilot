import type { AnalysisEvidence } from "@/lib/types";

export function EvidenceList({ evidence, emptyText }: { evidence: AnalysisEvidence[]; emptyText: string }) {
  if (evidence.length === 0) {
    return <p className="text-sm text-slate-500">{emptyText}</p>;
  }

  return (
    <ul className="space-y-2">
      {evidence.slice(0, 12).map((item, index) => (
        <li key={`${item.type}-${item.label}-${index}`} className="rounded-md border border-slate-200 bg-slate-50 px-3 py-2">
          <p className="text-sm font-medium text-slate-900">{item.label}</p>
          <p className="mt-1 text-sm leading-6 text-slate-600">{item.text}</p>
        </li>
      ))}
    </ul>
  );
}

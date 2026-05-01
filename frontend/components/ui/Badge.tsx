import { formatTitle } from "@/lib/format";

type BadgeTone = "neutral" | "success" | "warning" | "danger" | "info";

const toneClasses: Record<BadgeTone, string> = {
  neutral: "border-slate-200 bg-slate-50 text-slate-700",
  success: "border-emerald-200 bg-emerald-50 text-emerald-800",
  warning: "border-amber-200 bg-amber-50 text-amber-800",
  danger: "border-red-200 bg-red-50 text-red-800",
  info: "border-sky-200 bg-sky-50 text-sky-800",
};

export function Badge({ children, tone = "neutral" }: { children: string; tone?: BadgeTone }) {
  return (
    <span className={`inline-flex rounded-md border px-2.5 py-1 text-xs font-semibold ${toneClasses[tone]}`}>
      {formatTitle(children)}
    </span>
  );
}

export function ScoreBadge({ score }: { score: number | null | undefined }) {
  if (score === null || score === undefined) {
    return <Badge tone="neutral">Not available</Badge>;
  }

  const tone: BadgeTone = score >= 75 ? "success" : score >= 55 ? "warning" : "danger";
  return <Badge tone={tone}>{`${score}/100`}</Badge>;
}

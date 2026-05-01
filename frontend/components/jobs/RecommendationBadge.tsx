import { formatTitle } from "@/lib/format";
import type { AuthorizationRisk, Recommendation } from "@/lib/types";

const recommendationStyles: Record<Recommendation, string> = {
  apply: "border-emerald-200 bg-emerald-50 text-emerald-800",
  apply_with_caution: "border-amber-200 bg-amber-50 text-amber-800",
  maybe: "border-sky-200 bg-sky-50 text-sky-800",
  skip: "border-red-200 bg-red-50 text-red-800",
};

const riskStyles: Record<AuthorizationRisk, string> = {
  low: "border-emerald-200 bg-emerald-50 text-emerald-800",
  medium: "border-amber-200 bg-amber-50 text-amber-800",
  high: "border-red-200 bg-red-50 text-red-800",
  unknown: "border-slate-200 bg-slate-50 text-slate-700",
};

type Props =
  | { type: "recommendation"; value: Recommendation | null }
  | { type: "risk"; value: AuthorizationRisk };

export function RecommendationBadge(props: Props) {
  const value = props.value;
  if (!value) {
    return null;
  }

  const className =
    props.type === "recommendation" ? recommendationStyles[value as Recommendation] : riskStyles[value as AuthorizationRisk];

  return (
    <span className={`inline-flex items-center rounded-md border px-2.5 py-1 text-xs font-semibold ${className}`}>
      {formatTitle(value)}
    </span>
  );
}

function SkillPill({ value, tone }: { value: string; tone: "required" | "preferred" }) {
  const className =
    tone === "required"
      ? "border-red-200 bg-red-50 text-red-800"
      : "border-amber-200 bg-amber-50 text-amber-800";

  return <span className={`rounded-md border px-2 py-1 text-xs font-medium ${className}`}>{value}</span>;
}

export function MissingSkills({
  required,
  preferred,
  skillGapNote,
  technicalSkillCount,
  hasDomainSignals = false,
  requiredLabel = "Missing Required",
  preferredLabel = "Missing Preferred",
}: {
  required: string[];
  preferred: string[];
  skillGapNote?: string | null;
  technicalSkillCount?: number;
  hasDomainSignals?: boolean;
  requiredLabel?: string;
  preferredLabel?: string;
}) {
  if (required.length === 0 && preferred.length === 0) {
    if ((technicalSkillCount ?? 0) <= 2) {
      return (
        <p className="text-sm text-amber-800">
          {skillGapNote || "Limited structured technical requirements detected. Skill gap analysis may be incomplete."}
        </p>
      );
    }
    if (hasDomainSignals) {
      return (
        <p className="text-sm text-slate-600">
          No missing technical skills were detected, but domain/context signals may still require preparation.
        </p>
      );
    }
    return <p className="text-sm text-slate-600">No missing technical skills were detected from the extracted job requirements.</p>;
  }

  return (
    <div className="grid gap-4 md:grid-cols-2">
      <div>
        <h4 className="text-sm font-semibold text-slate-900">{requiredLabel}</h4>
        <div className="mt-2 flex flex-wrap gap-2">
          {required.length > 0 ? required.map((skill) => <SkillPill key={skill} value={skill} tone="required" />) : null}
          {required.length === 0 ? <p className="text-sm text-slate-500">None detected.</p> : null}
        </div>
      </div>
      <div>
        <h4 className="text-sm font-semibold text-slate-900">{preferredLabel}</h4>
        <div className="mt-2 flex flex-wrap gap-2">
          {preferred.length > 0
            ? preferred.map((skill) => <SkillPill key={skill} value={skill} tone="preferred" />)
            : null}
          {preferred.length === 0 ? <p className="text-sm text-slate-500">None detected.</p> : null}
        </div>
      </div>
    </div>
  );
}

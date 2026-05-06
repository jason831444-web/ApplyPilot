import type { ReactNode } from "react";
import { formatTitle } from "@/lib/format";
import type { JobAnalysis } from "@/lib/types";
import { EvidenceList } from "./EvidenceList";
import { MissingSkills } from "./MissingSkills";
import { RecommendationBadge } from "./RecommendationBadge";
import { ScoreCards } from "./ScoreCards";

function PillList({ values, emptyText }: { values: string[]; emptyText: string }) {
  if (values.length === 0) {
    return <p className="text-sm text-slate-500">{emptyText}</p>;
  }

  return (
    <div className="flex flex-wrap gap-2">
      {values.map((value) => (
        <span key={value} className="rounded-md border border-slate-200 bg-slate-50 px-2 py-1 text-xs font-medium text-slate-700">
          {value}
        </span>
      ))}
    </div>
  );
}

function TextList({ values, emptyText }: { values: string[]; emptyText: string }) {
  if (values.length === 0) {
    return <p className="text-sm text-slate-500">{emptyText}</p>;
  }

  return (
    <ul className="list-disc space-y-2 pl-5 text-sm leading-6 text-slate-700">
      {values.map((value) => (
        <li key={value}>{value}</li>
      ))}
    </ul>
  );
}

function CollapsibleSection({
  title,
  children,
  defaultOpen = false,
}: {
  title: string;
  children: ReactNode;
  defaultOpen?: boolean;
}) {
  return (
    <details className="rounded-md border border-slate-200 bg-white p-5" open={defaultOpen}>
      <summary className="cursor-pointer text-base font-semibold text-slate-950">{title}</summary>
      <div className="mt-3">{children}</div>
    </details>
  );
}

export function JobAnalysisView({ analysis }: { analysis: JobAnalysis }) {
  const technicalSkills = analysis.technical_skills ?? [...analysis.required_skills, ...analysis.preferred_skills];
  const domainSignals = analysis.domain_signals ?? [];
  const concerns = [...analysis.concerns];
  if (analysis.skill_extraction_confidence === "low" && concerns.length === 0) {
    const confidenceConcern = "Only limited structured technical requirements were detected, so match confidence is lower.";
    if (!concerns.includes(confidenceConcern)) {
      concerns.unshift(confidenceConcern);
    }
  }

  return (
    <div className="space-y-5">
      <div className="rounded-md border border-slate-200 bg-white p-5">
        <div className="flex flex-wrap items-start justify-between gap-3">
          <div>
            <p className="text-xs font-medium uppercase tracking-wide text-slate-500">Recommendation</p>
            <div className="mt-2 flex flex-wrap items-center gap-2">
              <RecommendationBadge type="recommendation" value={analysis.recommendation} />
              <RecommendationBadge type="risk" value={analysis.authorization_risk} />
            </div>
          </div>
          <div className="text-right">
            <p className="text-xs font-medium uppercase tracking-wide text-slate-500">Overall score</p>
            <p className="mt-1 text-3xl font-semibold text-slate-950">{analysis.overall_score}</p>
          </div>
        </div>
        <p className="mt-4 text-sm leading-6 text-slate-700">{analysis.recommendation_reason}</p>
        {analysis.summary ? <p className="mt-2 text-sm leading-6 text-slate-600">{analysis.summary}</p> : null}
      </div>

      <ScoreCards
        scores={[
          { label: "Required skills", value: analysis.required_skill_score },
          { label: "Preferred skills", value: analysis.preferred_skill_score },
          { label: "Resume match", value: analysis.resume_match_score },
          { label: "Experience fit", value: analysis.experience_fit_score },
          { label: "Location fit", value: analysis.location_fit_score },
          { label: "New-grad fit", value: analysis.new_grad_fit_score },
        ]}
      />

      <div className="grid gap-4 lg:grid-cols-2">
        <section className="rounded-md border border-slate-200 bg-white p-5">
          <h3 className="text-base font-semibold">New-Grad Fit</h3>
          <p className="mt-1 text-sm text-slate-600">
            {analysis.new_grad_fit_label ? formatTitle(analysis.new_grad_fit_label) : "Unknown"} ({analysis.new_grad_fit_score}/100)
          </p>
          <div className="mt-4 space-y-4">
            <EvidenceList evidence={analysis.new_grad_positive_signals} emptyText="No positive new-grad signals found." />
            <EvidenceList evidence={analysis.new_grad_negative_signals} emptyText="No negative seniority signals found." />
          </div>
        </section>

        <section className="rounded-md border border-slate-200 bg-white p-5">
          <h3 className="text-base font-semibold">Authorization Risk</h3>
          <p className="mt-1 text-sm text-slate-600">{formatTitle(analysis.authorization_risk)}</p>
          <div className="mt-4">
            <EvidenceList evidence={analysis.authorization_evidence} emptyText="No sponsorship or work authorization language found." />
          </div>
        </section>
      </div>

      <section className="rounded-md border border-slate-200 bg-white p-5">
        <h3 className="text-base font-semibold">Extracted Signals</h3>
        <div className="mt-4 grid gap-4 md:grid-cols-2">
          <div>
            <h4 className="text-sm font-semibold text-slate-900">Technical Skills</h4>
            <div className="mt-2">
              <PillList values={technicalSkills} emptyText="No technical skills detected." />
            </div>
          </div>
          <div>
            <h4 className="text-sm font-semibold text-slate-900">Domain Signals</h4>
            <div className="mt-2">
              <PillList values={domainSignals} emptyText="No domain signals detected." />
            </div>
          </div>
        </div>
        <div className="mt-5">
          <MissingSkills
            required={analysis.missing_technical_skills ?? analysis.missing_required_skills}
            preferred={analysis.missing_preferred_technical_skills ?? analysis.missing_preferred_skills}
            skillGapNote={analysis.skill_gap_note}
            technicalSkillCount={technicalSkills.length}
            hasDomainSignals={domainSignals.length > 0}
            requiredLabel="Missing Technical Skills"
            preferredLabel="Preferred Keywords To Consider"
          />
        </div>
      </section>

      <div className="grid gap-4 lg:grid-cols-2">
        <section className="rounded-md border border-slate-200 bg-white p-5">
          <h3 className="text-base font-semibold">Strengths</h3>
          <div className="mt-3">
            <TextList values={analysis.strengths} emptyText="No strengths detected." />
          </div>
        </section>
        <CollapsibleSection title="Concerns" defaultOpen={concerns.length > 0}>
          <TextList values={concerns} emptyText="No concerns detected." />
        </CollapsibleSection>
      </div>

      <section className="rounded-md border border-slate-200 bg-white p-5">
        <h3 className="text-base font-semibold">Next Actions</h3>
        <div className="mt-3">
          <TextList values={analysis.next_actions} emptyText="No next actions generated." />
        </div>
      </section>

      <CollapsibleSection title="Evidence">
        <EvidenceList evidence={analysis.evidence} emptyText="No evidence captured." />
      </CollapsibleSection>
    </div>
  );
}

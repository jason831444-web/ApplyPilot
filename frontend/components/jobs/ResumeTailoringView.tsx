"use client";

import { useState } from "react";
import { Button } from "@/components/ui/Button";
import type { ResumeTailoring } from "@/lib/types";

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

export function ResumeTailoringView({ tailoring }: { tailoring: ResumeTailoring }) {
  const [copyMessage, setCopyMessage] = useState<string | null>(null);

  async function copyText(text: string, label: string) {
    await navigator.clipboard.writeText(text);
    setCopyMessage(`${label} copied.`);
    window.setTimeout(() => setCopyMessage(null), 1800);
  }

  return (
    <section className="rounded-md border border-slate-200 bg-white p-5">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <h2 className="text-lg font-semibold text-slate-950">Resume Tailoring Suggestions</h2>
          <p className="mt-1 text-sm text-slate-600">
            Deterministic suggestions based on your profile, the job posting, and the saved analysis.
          </p>
        </div>
        {copyMessage ? <p className="text-sm font-medium text-emerald-700">{copyMessage}</p> : null}
      </div>

      <div className="mt-5 space-y-5">
        <div className="rounded-md border border-slate-200 bg-slate-50 p-4">
          <div className="flex flex-wrap items-center justify-between gap-3">
            <h3 className="text-sm font-semibold text-slate-900">Tailored Summary</h3>
            <Button
              onClick={() => copyText(tailoring.tailored_summary, "Summary")}
              type="button"
              variant="secondary"
            >
              Copy tailored summary
            </Button>
          </div>
          <p className="mt-3 text-sm leading-6 text-slate-700">{tailoring.tailored_summary}</p>
        </div>

        <div>
          <div className="flex flex-wrap items-center justify-between gap-3">
            <h3 className="text-sm font-semibold text-slate-900">Bullet Suggestions</h3>
            <Button
              disabled={tailoring.bullet_suggestions.length === 0}
              onClick={() => copyText(tailoring.bullet_suggestions.map((item) => `- ${item}`).join("\n"), "Bullets")}
              type="button"
              variant="secondary"
            >
              Copy all bullets
            </Button>
          </div>
          <div className="mt-3">
            <TextList values={tailoring.bullet_suggestions} emptyText="No bullet suggestions generated." />
          </div>
        </div>

        <div className="grid gap-4 md:grid-cols-2">
          <div>
            <h3 className="text-sm font-semibold text-slate-900">Skills to Emphasize</h3>
            <div className="mt-2">
              <PillList values={tailoring.skills_to_emphasize} emptyText="No matched skills found in the profile." />
            </div>
          </div>
          <div>
            <h3 className="text-sm font-semibold text-slate-900">Keywords to Consider</h3>
            <div className="mt-2">
              <PillList values={tailoring.keywords_to_add} emptyText="No missing keywords suggested." />
            </div>
          </div>
        </div>

        <div className="grid gap-4 md:grid-cols-2">
          <div>
            <h3 className="text-sm font-semibold text-slate-900">Project Suggestions</h3>
            <div className="mt-3">
              <TextList values={tailoring.project_suggestions} emptyText="No project suggestions generated." />
            </div>
          </div>
          <div>
            <h3 className="text-sm font-semibold text-slate-900">Cautions</h3>
            <div className="mt-3">
              <TextList values={tailoring.cautions} emptyText="No cautions generated." />
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}

"use client";

import { FormEvent, useEffect, useState } from "react";
import { useAuth } from "@/hooks/useAuth";
import { apiRequest } from "@/lib/api";
import type { Application, ApplicationStatus, ApplicationWithJob } from "@/lib/types";
import { Button } from "@/components/ui/Button";
import { Card, CardBody, CardHeader } from "@/components/ui/Card";
import { ErrorState } from "@/components/ui/State";
import { ApplicationStatusSelect } from "./ApplicationStatusSelect";

type Props = {
  jobId: number;
  application: Application | null;
  onSaved: (application: Application) => void;
};

function emptyToNull(value: string): string | null {
  const trimmed = value.trim();
  return trimmed ? trimmed : null;
}

export function ApplicationEditor({ jobId, application, onSaved }: Props) {
  const { token } = useAuth();
  const [status, setStatus] = useState<ApplicationStatus>(application?.status ?? "saved");
  const [appliedDate, setAppliedDate] = useState(application?.applied_date ?? "");
  const [notes, setNotes] = useState(application?.notes ?? "");
  const [nextAction, setNextAction] = useState(application?.next_action ?? "");
  const [nextActionDate, setNextActionDate] = useState(application?.next_action_date ?? "");
  const [isSaving, setIsSaving] = useState(false);
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    setStatus(application?.status ?? "saved");
    setAppliedDate(application?.applied_date ?? "");
    setNotes(application?.notes ?? "");
    setNextAction(application?.next_action ?? "");
    setNextActionDate(application?.next_action_date ?? "");
  }, [application]);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!token) {
      return;
    }

    setIsSaving(true);
    setMessage(null);
    setError(null);

    const body = {
      status,
      applied_date: emptyToNull(appliedDate),
      notes: emptyToNull(notes),
      next_action: emptyToNull(nextAction),
      next_action_date: emptyToNull(nextActionDate),
    };

    try {
      const saved = application
        ? await apiRequest<ApplicationWithJob>(`/api/applications/${application.id}`, {
            method: "PATCH",
            token,
            body,
          })
        : await apiRequest<Application>("/api/applications", {
            method: "POST",
            token,
            body: { job_id: jobId, ...body },
          });
      onSaved(saved);
      setMessage("Application tracking saved.");
      setAppliedDate(saved.applied_date ?? "");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to save application.");
    } finally {
      setIsSaving(false);
    }
  }

  return (
    <form onSubmit={handleSubmit}>
      <Card>
        <CardHeader
          title="Application Tracking"
          description="Track where this role sits in your pipeline."
          action={
            <Button type="submit" disabled={isSaving}>
              {isSaving ? "Saving..." : "Save Tracking"}
            </Button>
          }
        />

        <CardBody>
          {error ? <ErrorState message={error} /> : null}
          {message ? <p className="rounded-md bg-emerald-50 px-3 py-2 text-sm text-emerald-800">{message}</p> : null}

          <div className="mt-5 grid gap-4 md:grid-cols-2">
            <label className="block space-y-1 text-sm font-medium text-slate-700">
              <span>Status</span>
              <ApplicationStatusSelect value={status} onChange={setStatus} />
            </label>
            <label className="block space-y-1 text-sm font-medium text-slate-700">
              <span>Applied date</span>
              <input
                className="w-full rounded-md border border-slate-300 px-3 py-2 text-sm outline-none focus:border-slate-950"
                type="date"
                value={appliedDate}
                onChange={(event) => setAppliedDate(event.target.value)}
              />
            </label>
            <label className="block space-y-1 text-sm font-medium text-slate-700">
              <span>Next action</span>
              <input
                className="w-full rounded-md border border-slate-300 px-3 py-2 text-sm outline-none focus:border-slate-950"
                value={nextAction}
                onChange={(event) => setNextAction(event.target.value)}
                placeholder="Follow up, prep OA, update resume"
              />
            </label>
            <label className="block space-y-1 text-sm font-medium text-slate-700">
              <span>Next action date</span>
              <input
                className="w-full rounded-md border border-slate-300 px-3 py-2 text-sm outline-none focus:border-slate-950"
                type="date"
                value={nextActionDate}
                onChange={(event) => setNextActionDate(event.target.value)}
              />
            </label>
          </div>

          <label className="mt-4 block space-y-1 text-sm font-medium text-slate-700">
            <span>Notes</span>
            <textarea
              className="min-h-28 w-full rounded-md border border-slate-300 px-3 py-2 text-sm outline-none focus:border-slate-950"
              value={notes}
              onChange={(event) => setNotes(event.target.value)}
              placeholder="Recruiter name, application portal notes, interview prep reminders"
            />
          </label>
        </CardBody>
      </Card>
    </form>
  );
}

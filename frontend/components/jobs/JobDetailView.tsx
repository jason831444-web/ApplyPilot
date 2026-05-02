"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { ApplicationEditor } from "@/components/applications/ApplicationEditor";
import { Button } from "@/components/ui/Button";
import { ErrorState, LoadingState } from "@/components/ui/State";
import { useAuth } from "@/hooks/useAuth";
import { apiRequest, getResumeTailoring } from "@/lib/api";
import { formatTitle } from "@/lib/format";
import type { Application, Job, JobAnalysis, ResumeTailoring } from "@/lib/types";
import { JobAnalysisView } from "./JobAnalysisView";
import { ResumeTailoringView } from "./ResumeTailoringView";

function formatDate(value: string): string {
  return new Intl.DateTimeFormat("en", { dateStyle: "medium", timeStyle: "short" }).format(new Date(value));
}

function getReadableError(err: unknown, fallback = "Something went wrong."): string {
  return err instanceof Error && err.message ? err.message : fallback;
}

function isNotFoundMessage(message: string): boolean {
  return message.toLowerCase().includes("not found");
}

export function JobDetailView({ jobId }: { jobId: string }) {
  const { token } = useAuth();
  const [job, setJob] = useState<Job | null>(null);
  const [application, setApplication] = useState<Application | null>(null);
  const [analysis, setAnalysis] = useState<JobAnalysis | null>(null);
  const [resumeTailoring, setResumeTailoring] = useState<ResumeTailoring | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [analysisError, setAnalysisError] = useState<string | null>(null);
  const [tailoringError, setTailoringError] = useState<string | null>(null);

  useEffect(() => {
    if (!token) {
      return;
    }

    const authToken = token;
    let isMounted = true;

    async function loadJob() {
      setIsLoading(true);
      setError(null);
      try {
        const data = await apiRequest<Job>(`/api/jobs/${jobId}`, { token: authToken });
        if (isMounted) {
          setJob(data);
          setApplication(data.application ?? null);
          setAnalysis(data.analysis ?? null);
        }
        try {
          const analysisData = await apiRequest<JobAnalysis>(`/api/jobs/${jobId}/analysis`, { token: authToken });
          if (isMounted) {
            setAnalysis(analysisData);
            setAnalysisError(null);
          }
          try {
            const tailoringData = await getResumeTailoring(jobId, authToken);
            if (isMounted) {
              setResumeTailoring(tailoringData);
              setTailoringError(null);
            }
          } catch (err) {
            if (isMounted) {
              setResumeTailoring(null);
              setTailoringError(getReadableError(err, "Unable to load resume tailoring suggestions."));
            }
          }
        } catch (err) {
          if (isMounted) {
            const message = getReadableError(err, "Something went wrong.");
            setAnalysisError(isNotFoundMessage(message) ? null : message);
            setResumeTailoring(null);
            setTailoringError(null);
          }
        }
      } catch (err) {
        if (isMounted) {
          const message = getReadableError(err, "Something went wrong.");
          setError(isNotFoundMessage(message) ? "Job not found or you do not have access to this job." : message);
        }
      } finally {
        if (isMounted) {
          setIsLoading(false);
        }
      }
    }

    void loadJob();

    return () => {
      isMounted = false;
    };
  }, [jobId, token]);

  async function handleAnalyze() {
    if (!token) {
      return;
    }

    setIsAnalyzing(true);
    setAnalysisError(null);

    try {
      const data = await apiRequest<JobAnalysis>(`/api/jobs/${jobId}/analyze`, {
        method: "POST",
        token,
      });
      setAnalysis(data);
      try {
        const tailoringData = await getResumeTailoring(jobId, token);
        setResumeTailoring(tailoringData);
        setTailoringError(null);
      } catch (err) {
        setResumeTailoring(null);
        setTailoringError(getReadableError(err, "Unable to load resume tailoring suggestions."));
      }
    } catch (err) {
      setAnalysisError(getReadableError(err, "Something went wrong."));
    } finally {
      setIsAnalyzing(false);
    }
  }

  if (isLoading) {
    return <LoadingState label="Loading job..." />;
  }

  if (error) {
    return <ErrorState message={error} />;
  }

  if (!job) {
    return <ErrorState message="Job not found or you do not have access to this job." />;
  }

  return (
    <section className="space-y-6">
      <div className="space-y-3">
        <Link className="text-sm font-medium text-slate-600 underline" href="/jobs">
          Back to jobs
        </Link>
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div>
            <h1 className="text-2xl font-semibold">{job.job_title}</h1>
            <p className="text-slate-600">
              {job.company_name} {job.location ? `- ${job.location}` : ""}
            </p>
          </div>
          {analysis ? (
            <div className="rounded-md border border-slate-200 bg-white px-4 py-3 text-right">
              <p className="text-xs font-medium uppercase tracking-wide text-slate-500">Overall score</p>
              <p className="text-2xl font-semibold text-slate-950">{analysis.overall_score}</p>
            </div>
          ) : null}
        </div>
      </div>

      <div className="grid gap-4 md:grid-cols-3">
        <div className="rounded-md border border-slate-200 bg-white p-4">
          <p className="text-xs font-medium uppercase tracking-wide text-slate-500">Created</p>
          <p className="mt-1 text-sm text-slate-900">{formatDate(job.created_at)}</p>
        </div>
        <div className="rounded-md border border-slate-200 bg-white p-4">
          <p className="text-xs font-medium uppercase tracking-wide text-slate-500">Source</p>
          <p className="mt-1 text-sm text-slate-900">{formatTitle(job.source_type)}</p>
        </div>
        <div className="rounded-md border border-slate-200 bg-white p-4">
          <p className="text-xs font-medium uppercase tracking-wide text-slate-500">Application status</p>
          <p className="mt-1 text-sm text-slate-900">
            {application ? formatTitle(application.status) : "No application record"}
          </p>
        </div>
      </div>

      {job.source_url ? (
        <p className="text-sm text-slate-600">
          Source URL:{" "}
          <a className="font-medium text-slate-950 underline" href={job.source_url} rel="noreferrer" target="_blank">
            {job.source_url}
          </a>
        </p>
      ) : null}

      <div className="space-y-4">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <h2 className="text-lg font-semibold">Analysis</h2>
          <Button variant="secondary" type="button" onClick={handleAnalyze} disabled={isAnalyzing}>
            {isAnalyzing ? "Analyzing..." : "Re-run Analysis"}
          </Button>
        </div>

        {analysisError ? <p className="rounded-md bg-amber-50 px-3 py-2 text-sm text-amber-800">{analysisError}</p> : null}
        {analysis ? (
          <JobAnalysisView analysis={analysis} />
        ) : (
          <div className="rounded-md border border-slate-200 bg-white p-5">
            <p className="text-sm text-slate-600">No analysis exists yet. Run analysis to generate job-fit results.</p>
          </div>
        )}
      </div>

      {analysis ? (
        resumeTailoring ? (
          <ResumeTailoringView tailoring={resumeTailoring} />
        ) : (
          <div className="rounded-md border border-slate-200 bg-white p-5">
            <h2 className="text-lg font-semibold">Resume Tailoring Suggestions</h2>
            <p className="mt-2 text-sm text-slate-600">
              {tailoringError || "Resume tailoring suggestions are not available yet."}
            </p>
          </div>
        )
      ) : null}

      <ApplicationEditor
        jobId={job.id}
        application={application}
        onSaved={(savedApplication) => setApplication(savedApplication)}
      />

      <div className="rounded-md border border-slate-200 bg-white p-5">
        <h2 className="text-lg font-semibold">Job Description</h2>
        <pre className="mt-4 whitespace-pre-wrap break-words text-sm leading-6 text-slate-700">{job.job_description}</pre>
      </div>
    </section>
  );
}

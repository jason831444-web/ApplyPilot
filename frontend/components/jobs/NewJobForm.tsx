"use client";

import { useRouter } from "next/navigation";
import { FormEvent, useState } from "react";
import { useAuth } from "@/hooks/useAuth";
import { apiRequest } from "@/lib/api";
import type { AnalyzeNewJobResponse, JobSourceType } from "@/lib/types";
import { Button } from "@/components/ui/Button";
import { ErrorState } from "@/components/ui/State";
import { PageHeader } from "@/components/ui/PageHeader";

export function NewJobForm() {
  const router = useRouter();
  const { token } = useAuth();
  const [companyName, setCompanyName] = useState("");
  const [jobTitle, setJobTitle] = useState("");
  const [location, setLocation] = useState("");
  const [sourceUrl, setSourceUrl] = useState("");
  const [jobDescription, setJobDescription] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!token) {
      return;
    }

    setError(null);
    if (companyName.trim().length === 0 || jobTitle.trim().length === 0) {
      setError("Company name and job title are required.");
      return;
    }
    if (jobDescription.trim().length < 20) {
      setError("Job description must be at least 20 characters.");
      return;
    }
    if (jobDescription.length > 50000) {
      setError("Job description must be 50,000 characters or fewer.");
      return;
    }
    setIsSubmitting(true);

    const sourceType: JobSourceType = sourceUrl.trim() ? "url" : "manual";

    try {
      const response = await apiRequest<AnalyzeNewJobResponse>("/api/jobs/analyze-new", {
        method: "POST",
        token,
        body: {
          company_name: companyName,
          job_title: jobTitle,
          location,
          source_url: sourceUrl || null,
          source_type: sourceType,
          job_description: jobDescription,
        },
      });
      router.push(`/jobs/${response.job.id}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to create job.");
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <form className="max-w-4xl space-y-6" onSubmit={handleSubmit}>
      <PageHeader
        title="Analyze New Job"
        description="Paste a job description. ApplyPilot will save it, compare it against your profile, and generate a recommendation."
      />

      {error ? <ErrorState message={error} /> : null}

      <div className="rounded-md border border-slate-200 bg-white p-5">
        <div className="grid gap-5 md:grid-cols-2">
          <label className="block space-y-1 text-sm font-medium text-slate-700">
            <span>Company name</span>
            <input
              className="w-full rounded-md border border-slate-300 px-3 py-2 outline-none focus:border-slate-950"
              value={companyName}
              onChange={(event) => setCompanyName(event.target.value)}
              maxLength={255}
              required
            />
          </label>
          <label className="block space-y-1 text-sm font-medium text-slate-700">
            <span>Job title</span>
            <input
              className="w-full rounded-md border border-slate-300 px-3 py-2 outline-none focus:border-slate-950"
              value={jobTitle}
              onChange={(event) => setJobTitle(event.target.value)}
              maxLength={255}
              required
            />
          </label>
          <label className="block space-y-1 text-sm font-medium text-slate-700">
            <span>Location</span>
            <input
              className="w-full rounded-md border border-slate-300 px-3 py-2 outline-none focus:border-slate-950"
            value={location}
            onChange={(event) => setLocation(event.target.value)}
            placeholder="New York, NY or Remote"
            maxLength={255}
          />
          </label>
          <label className="block space-y-1 text-sm font-medium text-slate-700">
            <span>Source URL</span>
            <input
              className="w-full rounded-md border border-slate-300 px-3 py-2 outline-none focus:border-slate-950"
              type="url"
              value={sourceUrl}
              onChange={(event) => setSourceUrl(event.target.value)}
              placeholder="https://example.com/job"
              maxLength={2000}
            />
          </label>
        </div>

      <label className="mt-5 block space-y-1 text-sm font-medium text-slate-700">
        <span>Job description</span>
        <textarea
          className="min-h-80 w-full rounded-md border border-slate-300 px-3 py-2 outline-none focus:border-slate-950"
          value={jobDescription}
          onChange={(event) => setJobDescription(event.target.value)}
          placeholder="Paste the full job description here."
          minLength={20}
          maxLength={50000}
          required
        />
        <span className="block text-xs font-normal text-slate-500">
          {jobDescription.length.toLocaleString()} / 50,000 characters
        </span>
      </label>
      </div>

      <Button type="submit" disabled={isSubmitting}>
        {isSubmitting ? "Analyzing..." : "Analyze Job"}
      </Button>
    </form>
  );
}

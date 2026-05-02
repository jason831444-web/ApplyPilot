"use client";

import { FormEvent, useEffect, useMemo, useState } from "react";
import { useAuth } from "@/hooks/useAuth";
import { apiRequest, uploadResume } from "@/lib/api";
import type { Profile, ProfileUpdate } from "@/lib/types";
import { Button } from "@/components/ui/Button";
import { Card, CardBody, CardHeader } from "@/components/ui/Card";
import { ErrorState, LoadingState } from "@/components/ui/State";
import { PageHeader } from "@/components/ui/PageHeader";

function parseCommaList(value: string): string[] {
  return value
    .split(",")
    .map((item) => item.trim())
    .filter(Boolean);
}

function parseLineList(value: string): string[] {
  return value
    .split(/\r?\n/)
    .map((item) => item.trim())
    .filter(Boolean);
}

function joinCommaList(value: string[]): string {
  return value.join(", ");
}

function joinLineList(value: string[]): string {
  return value.join("\n");
}

export function ProfileForm() {
  const { token } = useAuth();
  const [profile, setProfile] = useState<Profile | null>(null);
  const [resumeText, setResumeText] = useState("");
  const [skillsInput, setSkillsInput] = useState("");
  const [projectsInput, setProjectsInput] = useState("");
  const [experienceSummary, setExperienceSummary] = useState("");
  const [targetRolesInput, setTargetRolesInput] = useState("");
  const [targetLocationsInput, setTargetLocationsInput] = useState("");
  const [graduationDate, setGraduationDate] = useState("");
  const [workAuthorizationNotes, setWorkAuthorizationNotes] = useState("");
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);
  const [isUploadingResume, setIsUploadingResume] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  useEffect(() => {
    if (!token) {
      return;
    }

    let isMounted = true;

    async function loadProfile() {
      setIsLoading(true);
      setError(null);
      try {
        const data = await apiRequest<Profile>("/api/profile/me", { token });
        if (!isMounted) {
          return;
        }
        setProfile(data);
        setResumeText(data.resume_text ?? "");
        setSkillsInput(joinCommaList(data.skills ?? []));
        setProjectsInput(joinLineList(data.projects ?? []));
        setExperienceSummary(data.experience_summary ?? "");
        setTargetRolesInput(joinCommaList(data.target_roles ?? []));
        setTargetLocationsInput(joinCommaList(data.target_locations ?? []));
        setGraduationDate(data.graduation_date ?? "");
        setWorkAuthorizationNotes(data.work_authorization_notes ?? "");
      } catch (err) {
        if (isMounted) {
          setError(err instanceof Error ? err.message : "Unable to load profile.");
        }
      } finally {
        if (isMounted) {
          setIsLoading(false);
        }
      }
    }

    void loadProfile();

    return () => {
      isMounted = false;
    };
  }, [token]);

  const helperText = useMemo(
    () => "ApplyPilot will use this profile to compare your resume, skills, roles, locations, and authorization notes against job descriptions.",
    [],
  );

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!token) {
      return;
    }

    const payload: ProfileUpdate = {
      resume_text: resumeText,
      skills: parseCommaList(skillsInput),
      projects: parseLineList(projectsInput),
      experience_summary: experienceSummary,
      target_roles: parseCommaList(targetRolesInput),
      target_locations: parseCommaList(targetLocationsInput),
      graduation_date: graduationDate || null,
      work_authorization_notes: workAuthorizationNotes,
    };

    setIsSaving(true);
    setError(null);
    setSuccess(null);

    if (resumeText.length > 30000) {
      setError("Resume text must be 30,000 characters or fewer.");
      setIsSaving(false);
      return;
    }
    if (experienceSummary.length > 5000) {
      setError("Experience summary must be 5,000 characters or fewer.");
      setIsSaving(false);
      return;
    }
    if (workAuthorizationNotes.length > 2000) {
      setError("Work authorization notes must be 2,000 characters or fewer.");
      setIsSaving(false);
      return;
    }

    try {
      const data = await apiRequest<Profile>("/api/profile/me", {
        method: "PUT",
        token,
        body: payload,
      });
      setProfile(data);
      setSuccess("Profile saved.");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to save profile.");
    } finally {
      setIsSaving(false);
    }
  }

  async function handleResumeUpload(file: File | undefined) {
    if (!file || !token) {
      return;
    }
    if (file.type !== "application/pdf" && !file.name.toLowerCase().endsWith(".pdf")) {
      setError("Please upload a PDF resume.");
      return;
    }

    setIsUploadingResume(true);
    setError(null);
    setSuccess(null);
    try {
      const result = await uploadResume(file, token);
      const confirmed = window.confirm(
        "Replace resume text, skills, projects, and experience summary with suggestions from this PDF?",
      );
      if (!confirmed) {
        setSuccess("Resume parsed. No profile fields were changed.");
        return;
      }
      setResumeText(result.resume_text);
      if (result.skills_suggestions.length > 0) {
        setSkillsInput(joinCommaList(result.skills_suggestions));
      }
      if (result.projects_suggestions.length > 0) {
        setProjectsInput(joinLineList(result.projects_suggestions));
      }
      if (result.experience_summary_suggestion) {
        setExperienceSummary(result.experience_summary_suggestion);
      }
      setSuccess(
        `Imported ${result.skills_suggestions.length} skills and ${result.projects_suggestions.length} projects from your resume. Review the suggestions, then save your profile.`,
      );
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to import resume.");
    } finally {
      setIsUploadingResume(false);
    }
  }

  if (isLoading) {
    return <LoadingState label="Loading profile..." />;
  }

  return (
    <form className="max-w-5xl space-y-6" onSubmit={handleSubmit}>
      <PageHeader title="Profile" description={helperText} />

      {error ? <ErrorState message={error} /> : null}
      {success ? <p className="rounded-md bg-green-50 px-3 py-2 text-sm text-green-700">{success}</p> : null}

      <Card>
        <CardHeader
          title="Resume"
          description="Paste resume text or import a text-based PDF. Import suggestions are not saved until you click Save Profile."
          action={
            <label className="inline-flex cursor-pointer items-center justify-center rounded-md border border-slate-300 bg-white px-4 py-2 text-sm font-medium text-slate-900 transition hover:bg-slate-50">
              {isUploadingResume ? "Uploading..." : "Upload Resume (PDF)"}
              <input
                accept="application/pdf,.pdf"
                className="sr-only"
                disabled={isUploadingResume}
                onChange={(event) => {
                  void handleResumeUpload(event.target.files?.[0]);
                  event.target.value = "";
                }}
                type="file"
              />
            </label>
          }
        />
        <CardBody className="space-y-4">
          <label className="block space-y-1 text-sm font-medium text-slate-700">
            <span>Resume text</span>
            <textarea
              className="min-h-56 w-full rounded-md border border-slate-300 px-3 py-2 outline-none focus:border-slate-950"
              value={resumeText}
              onChange={(event) => setResumeText(event.target.value)}
              placeholder="Paste your resume text here."
              maxLength={30000}
            />
            <span className="block text-xs font-normal text-slate-500">
              {resumeText.length.toLocaleString()} / 30,000 characters
            </span>
          </label>
          <label className="block space-y-1 text-sm font-medium text-slate-700">
            <span>Experience summary</span>
            <textarea
              className="min-h-28 w-full rounded-md border border-slate-300 px-3 py-2 outline-none focus:border-slate-950"
              value={experienceSummary}
              onChange={(event) => setExperienceSummary(event.target.value)}
              placeholder="Summarize internships, research, coursework, and notable experience."
              maxLength={5000}
            />
          </label>
        </CardBody>
      </Card>

      <Card>
        <CardHeader title="Skills" description="Comma-separated skills are used for required and preferred skill matching." />
        <CardBody>
          <label className="block space-y-1 text-sm font-medium text-slate-700">
            <span>Skills</span>
            <input
              className="w-full rounded-md border border-slate-300 px-3 py-2 outline-none focus:border-slate-950"
              value={skillsInput}
              onChange={(event) => setSkillsInput(event.target.value)}
              placeholder="Python, React, PostgreSQL"
              maxLength={5000}
            />
            <span className="block text-xs font-normal text-slate-500">Separate skills with commas.</span>
          </label>
        </CardBody>
      </Card>

      <Card>
        <CardHeader title="Projects" description="Projects give the matcher additional evidence beyond your skills list." />
        <CardBody>
          <label className="block space-y-1 text-sm font-medium text-slate-700">
            <span>Projects</span>
            <textarea
              className="min-h-32 w-full rounded-md border border-slate-300 px-3 py-2 outline-none focus:border-slate-950"
              value={projectsInput}
              onChange={(event) => setProjectsInput(event.target.value)}
              placeholder="One project per line."
              maxLength={15000}
            />
            <span className="block text-xs font-normal text-slate-500">Use one line per project for the MVP.</span>
          </label>
        </CardBody>
      </Card>

      <Card>
        <CardHeader title="Target Roles And Locations" description="These fields power location fit and role relevance signals." />
        <CardBody className="grid gap-5 md:grid-cols-3">
          <label className="block space-y-1 text-sm font-medium text-slate-700">
            <span>Target roles</span>
            <input
              className="w-full rounded-md border border-slate-300 px-3 py-2 outline-none focus:border-slate-950"
              value={targetRolesInput}
              onChange={(event) => setTargetRolesInput(event.target.value)}
              placeholder="Software Engineer, Backend Engineer"
              maxLength={3000}
            />
            <span className="block text-xs font-normal text-slate-500">Separate roles with commas.</span>
          </label>
          <label className="block space-y-1 text-sm font-medium text-slate-700">
            <span>Target locations</span>
            <input
              className="w-full rounded-md border border-slate-300 px-3 py-2 outline-none focus:border-slate-950"
              value={targetLocationsInput}
              onChange={(event) => setTargetLocationsInput(event.target.value)}
              placeholder="New York, Remote, Seattle"
              maxLength={3000}
            />
            <span className="block text-xs font-normal text-slate-500">Separate locations with commas.</span>
          </label>
          <label className="block space-y-1 text-sm font-medium text-slate-700">
            <span>Graduation date</span>
            <input
              className="w-full rounded-md border border-slate-300 px-3 py-2 outline-none focus:border-slate-950"
              type="date"
              value={graduationDate}
              onChange={(event) => setGraduationDate(event.target.value)}
            />
          </label>
        </CardBody>
      </Card>

      <Card>
        <CardHeader title="Work Authorization" description="Used only to flag sponsorship or authorization risk from job postings." />
        <CardBody>
          <label className="block space-y-1 text-sm font-medium text-slate-700">
            <span>Work authorization notes</span>
            <textarea
              className="min-h-28 w-full rounded-md border border-slate-300 px-3 py-2 outline-none focus:border-slate-950"
              value={workAuthorizationNotes}
              onChange={(event) => setWorkAuthorizationNotes(event.target.value)}
              placeholder="Example: F-1 OPT eligible, may need H-1B sponsorship later."
              maxLength={2000}
            />
          </label>
        </CardBody>
      </Card>

      <div className="flex items-center gap-3">
        <Button type="submit" disabled={isSaving}>
          {isSaving ? "Saving..." : "Save Profile"}
        </Button>
        {profile ? <span className="text-xs text-slate-500">Profile ID {profile.id}</span> : null}
      </div>
    </form>
  );
}

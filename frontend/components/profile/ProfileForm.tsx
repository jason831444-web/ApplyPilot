"use client";

import { FormEvent, useEffect, useMemo, useState } from "react";
import { useAuth } from "@/hooks/useAuth";
import { apiRequest } from "@/lib/api";
import type { Profile, ProfileUpdate } from "@/lib/types";

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

  if (isLoading) {
    return <p className="text-sm text-slate-600">Loading profile...</p>;
  }

  return (
    <form className="max-w-4xl space-y-6" onSubmit={handleSubmit}>
      <div className="space-y-2">
        <h1 className="text-2xl font-semibold">Profile</h1>
        <p className="max-w-3xl text-sm text-slate-600">{helperText}</p>
      </div>

      {error ? <p className="rounded-md bg-red-50 px-3 py-2 text-sm text-red-700">{error}</p> : null}
      {success ? <p className="rounded-md bg-green-50 px-3 py-2 text-sm text-green-700">{success}</p> : null}

      <label className="block space-y-1 text-sm font-medium text-slate-700">
        <span>Resume text</span>
        <textarea
          className="min-h-56 w-full rounded-md border border-slate-300 px-3 py-2 outline-none focus:border-slate-950"
          value={resumeText}
          onChange={(event) => setResumeText(event.target.value)}
          placeholder="Paste your resume text here."
        />
      </label>

      <div className="grid gap-5 md:grid-cols-2">
        <label className="block space-y-1 text-sm font-medium text-slate-700">
          <span>Skills</span>
          <input
            className="w-full rounded-md border border-slate-300 px-3 py-2 outline-none focus:border-slate-950"
            value={skillsInput}
            onChange={(event) => setSkillsInput(event.target.value)}
            placeholder="Python, React, PostgreSQL"
          />
          <span className="block text-xs font-normal text-slate-500">Separate skills with commas.</span>
        </label>

        <label className="block space-y-1 text-sm font-medium text-slate-700">
          <span>Target roles</span>
          <input
            className="w-full rounded-md border border-slate-300 px-3 py-2 outline-none focus:border-slate-950"
            value={targetRolesInput}
            onChange={(event) => setTargetRolesInput(event.target.value)}
            placeholder="Software Engineer, Backend Engineer"
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
      </div>

      <label className="block space-y-1 text-sm font-medium text-slate-700">
        <span>Projects</span>
        <textarea
          className="min-h-32 w-full rounded-md border border-slate-300 px-3 py-2 outline-none focus:border-slate-950"
          value={projectsInput}
          onChange={(event) => setProjectsInput(event.target.value)}
          placeholder="One project per line."
        />
        <span className="block text-xs font-normal text-slate-500">Use one line per project for the MVP.</span>
      </label>

      <label className="block space-y-1 text-sm font-medium text-slate-700">
        <span>Experience summary</span>
        <textarea
          className="min-h-28 w-full rounded-md border border-slate-300 px-3 py-2 outline-none focus:border-slate-950"
          value={experienceSummary}
          onChange={(event) => setExperienceSummary(event.target.value)}
          placeholder="Summarize internships, research, coursework, and notable experience."
        />
      </label>

      <label className="block space-y-1 text-sm font-medium text-slate-700">
        <span>Work authorization notes</span>
        <textarea
          className="min-h-28 w-full rounded-md border border-slate-300 px-3 py-2 outline-none focus:border-slate-950"
          value={workAuthorizationNotes}
          onChange={(event) => setWorkAuthorizationNotes(event.target.value)}
          placeholder="Example: F-1 OPT eligible, may need H-1B sponsorship later."
        />
      </label>

      <div className="flex items-center gap-3">
        <button
          className="rounded-md bg-slate-950 px-4 py-2 text-sm font-medium text-white disabled:cursor-not-allowed disabled:bg-slate-400"
          type="submit"
          disabled={isSaving}
        >
          {isSaving ? "Saving..." : "Save Profile"}
        </button>
        {profile ? <span className="text-xs text-slate-500">Profile ID {profile.id}</span> : null}
      </div>
    </form>
  );
}

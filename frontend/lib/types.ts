export type Recommendation = "apply" | "apply_with_caution" | "maybe" | "skip";

export type User = {
  id: number;
  email: string;
  full_name: string;
};

export type TokenResponse = {
  access_token: string;
  token_type: "bearer";
  user: User;
};

export type Profile = {
  id: number;
  user_id: number;
  resume_text: string;
  skills: string[];
  projects: string[];
  experience_summary: string;
  target_roles: string[];
  target_locations: string[];
  graduation_date: string | null;
  work_authorization_notes: string;
};

export type ProfileUpdate = Omit<Profile, "id" | "user_id">;

export type ApplicationStatus =
  | "saved"
  | "applied"
  | "online_assessment"
  | "recruiter_screen"
  | "technical_interview"
  | "final_interview"
  | "offer"
  | "rejected"
  | "withdrawn"
  | "archived";

export type Application = {
  id: number;
  user_id: number;
  job_id: number;
  status: ApplicationStatus;
  applied_date: string | null;
  notes: string | null;
  next_action: string | null;
  next_action_date: string | null;
};

export type JobSourceType = "manual" | "url";

export type Job = {
  id: number;
  user_id: number;
  company_name: string;
  job_title: string;
  location: string;
  job_description: string;
  source_url: string | null;
  source_type: JobSourceType;
  created_at: string;
  updated_at: string;
  application?: Application | null;
};

export type AnalyzeNewJobResponse = {
  job: Job;
  application: Application;
};

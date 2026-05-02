export type Recommendation = "apply" | "apply_with_caution" | "maybe" | "skip";
export type AuthorizationRisk = "low" | "medium" | "high" | "unknown";
export type NewGradFitLabel = "strong_fit" | "good_fit" | "mixed_fit" | "weak_fit" | "not_new_grad_friendly";

export type AnalysisEvidence = {
  type: string;
  label: string;
  text: string;
  source?: string;
  polarity?: string;
  severity?: number;
};

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
  created_at: string;
  updated_at: string;
};

export type ApplicationJobSummary = {
  id: number;
  company_name: string;
  job_title: string;
  location: string | null;
};

export type ApplicationAnalysisSummary = {
  overall_score: number;
  recommendation: Recommendation | null;
  authorization_risk: AuthorizationRisk;
  new_grad_fit_label: NewGradFitLabel | null;
};

export type ApplicationWithJob = Application & {
  job: ApplicationJobSummary;
  analysis: ApplicationAnalysisSummary | null;
};

export type JobSourceType = "manual" | "url";

export type JobAnalysis = {
  id: number;
  job_id: number;
  user_id: number;
  parsed_title: string | null;
  parsed_company: string | null;
  parsed_locations: string[];
  employment_type: string | null;
  seniority_signals: AnalysisEvidence[];
  required_skills: string[];
  preferred_skills: string[];
  technical_skills: string[];
  domain_signals: string[];
  experience_requirements: AnalysisEvidence[];
  overall_score: number;
  new_grad_fit_score: number;
  resume_match_score: number;
  required_skill_score: number;
  preferred_skill_score: number;
  experience_fit_score: number;
  location_fit_score: number;
  new_grad_fit_label: NewGradFitLabel | null;
  authorization_risk: AuthorizationRisk;
  recommendation: Recommendation | null;
  recommendation_reason: string | null;
  summary: string | null;
  strengths: string[];
  concerns: string[];
  missing_required_skills: string[];
  missing_preferred_skills: string[];
  missing_technical_skills: string[];
  missing_domain_signals: string[];
  new_grad_positive_signals: AnalysisEvidence[];
  new_grad_negative_signals: AnalysisEvidence[];
  authorization_evidence: AnalysisEvidence[];
  evidence: AnalysisEvidence[];
  next_actions: string[];
  analysis_provider: string;
  analysis_confidence: number | null;
  fallback_used: boolean;
  created_at: string;
  updated_at: string;
};

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
  analysis?: JobAnalysis | null;
};

export type AnalyzeNewJobResponse = {
  job: Job;
  application: Application;
  analysis: JobAnalysis;
};

export type BulkDeleteResponse = {
  deleted_count: number;
};

export type ResumeTailoring = {
  tailored_summary: string;
  bullet_suggestions: string[];
  keywords_to_add: string[];
  skills_to_emphasize: string[];
  project_suggestions: string[];
  cautions: string[];
};

export type DistributionItem = {
  label: string;
  count: number;
};

export type MissingSkillItem = {
  skill: string;
  count: number;
};

export type UpcomingFollowup = {
  application_id: number;
  job_id: number;
  company_name: string;
  job_title: string;
  status: ApplicationStatus;
  next_action: string | null;
  next_action_date: string;
};

export type BestOpportunity = {
  job_id: number;
  application_id: number | null;
  company_name: string;
  job_title: string;
  location: string | null;
  status: ApplicationStatus | null;
  overall_score: number;
  recommendation: Recommendation | null;
  authorization_risk: AuthorizationRisk;
  new_grad_fit_label: NewGradFitLabel | null;
};

export type CautionReason = {
  reason: string;
  count: number;
};

export type DashboardSummary = {
  total_jobs: number;
  total_applications: number;
  saved_count: number;
  applied_count: number;
  interview_count: number;
  rejected_count: number;
  offer_count: number;
  average_match_score: number | null;
  applications_by_status: DistributionItem[];
  recommendation_distribution: DistributionItem[];
  authorization_risk_distribution: DistributionItem[];
  new_grad_fit_distribution: DistributionItem[];
  top_missing_skills: MissingSkillItem[];
  upcoming_followups: UpcomingFollowup[];
  best_opportunities: BestOpportunity[];
  caution_reasons: CautionReason[];
  next_recommended_actions: string[];
};

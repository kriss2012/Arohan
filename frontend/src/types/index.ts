export type UserRole = 
  | "SUPER_ADMIN"
  | "INSTITUTE_ADMIN"
  | "HOD"
  | "FACULTY"
  | "EXAM_CONTROLLER"
  | "PLACEMENT_OFFICER"
  | "MENTOR"
  | "STUDENT";

export interface UserSummary {
  id: string;
  email: string;
  first_name: string;
  last_name: string;
  roles: UserRole[];
  department_name?: string;
  institution_code: string;
}

export interface Resource {
  id: string;
  title: string;
  resource_type: string;
  file_url?: string;
  content_text?: string;
}

export interface Topic {
  id: string;
  title: string;
  learning_objective?: string;
  sequence_order: number;
  resources: Resource[];
  status?: string;
}

export interface Unit {
  id: string;
  unit_number: number;
  title: string;
  topics: Topic[];
}

export interface Subject {
  id: string;
  name: string;
  code: string;
  credits: number;
  units: Unit[];
}

export interface QuestionOption {
  id: string;
  option_key: string;
  option_text: string;
}

export interface Question {
  id: string;
  category: string;
  subcategory: string;
  difficulty: number;
  question_type: string;
  question_text: string;
  options: QuestionOption[];
}

export interface MCATExam {
  id: string;
  title: string;
  exam_code: string;
  mode: string;
  total_questions: number;
  time_limit_minutes: number;
  is_published: boolean;
}

export interface AttemptResponse {
  question_id: string;
  selected_option_id?: string;
  is_marked_for_review: boolean;
}

export interface AttemptData {
  id: string;
  exam_id: string;
  exam_title: string;
  status: string;
  remaining_seconds: number;
  total_questions: number;
  questions: Question[];
  saved_responses: AttemptResponse[];
}

export interface ScoreResult {
  attempt_id: string;
  status: string;
  score_raw: number;
  score_percentage: number;
  total_correct: number;
  total_incorrect: number;
  total_unanswered: number;
  category_scores: Record<string, number>;
  integrity_signal_count: number;
}

export interface Recommendation {
  id: string;
  skill_id: string;
  skill_name: string;
  category: string;
  action_type: string;
  title: string;
  evidence_summary: string;
  mathematical_rationale?: string;
  why_endpoint: string;
  is_completed: boolean;
}

export interface SkillCompetency {
  skill_id: string;
  skill_name: string;
  category: string;
  mastery_probability: number;
  confidence_score: number;
  evidence_count: number;
  status_label: string;
}

export interface EvidenceDrawerData {
  skill_id: string;
  skill_name: string;
  category: string;
  mastery_probability: number;
  confidence_score: number;
  evidence_count: number;
  correct_count: number;
  incorrect_count: number;
  gap_score: number;
  recommendation_logic: string;
  recent_evidence_events: Array<{
    event_type: string;
    source: string;
    timestamp: string;
  }>;
}

export interface CandidateMonitor {
  attempt_id: string;
  student_id: string;
  student_name: string;
  student_email: string;
  status: string;
  remaining_seconds: number;
  score_percentage: number;
  integrity_signal_count: number;
}

export interface LiveMonitorData {
  active_candidates_count: number;
  status_distribution: Record<string, number>;
  integrity_signal_severity: Record<string, number>;
  candidates: CandidateMonitor[];
  recent_integrity_signals: Array<{
    id: string;
    attempt_id: string;
    event_type: string;
    severity: string;
    timestamp: string;
    details?: string;
  }>;
}

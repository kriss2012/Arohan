import { 
  UserSummary, Subject, MCATExam, AttemptData, 
  ScoreResult, Recommendation, SkillCompetency, 
  EvidenceDrawerData, LiveMonitorData 
} from "../types";

const API_BASE = (typeof window !== "undefined" && window.location.origin.startsWith("http"))
  ? `${window.location.origin}/api/v1`
  : "http://127.0.0.1:8000/api/v1";

class ApiClient {
  private token: string | null = localStorage.getItem("isdp_token");
  public serverTime: string = new Date().toISOString();

  setToken(token: string | null) {
    this.token = token;
    if (token) {
      localStorage.setItem("isdp_token", token);
    } else {
      localStorage.removeItem("isdp_token");
    }
  }

  getToken(): string | null {
    return this.token;
  }

  private async request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
    const headers: Record<string, string> = {
      "Content-Type": "application/json",
      ...(options.headers as Record<string, string> || {})
    };

    if (this.token) {
      headers["Authorization"] = `Bearer ${this.token}`;
    }

    const response = await fetch(`${API_BASE}${endpoint}`, {
      ...options,
      headers
    });

    const serverTimeHeader = response.headers.get("X-Server-Time-UTC");
    if (serverTimeHeader) {
      this.serverTime = serverTimeHeader;
    }

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({ detail: "Unknown network error" }));
      throw new Error(errorData.detail || `Request failed with status ${response.status}`);
    }

    return response.json();
  }

  // Production Authentication Lifecycle
  async checkEmail(email: string): Promise<{ status: string; message: string; masked_email?: string; first_name?: string }> {
    return this.request("/auth/check-email", {
      method: "POST",
      body: JSON.stringify({ email })
    });
  }

  async sendCode(email: string): Promise<{ message: string; masked_email: string; expires_in_seconds: number }> {
    return this.request("/auth/send-code", {
      method: "POST",
      body: JSON.stringify({ email })
    });
  }

  async verifyCode(email: string, code: string): Promise<{ setup_token: string; message: string }> {
    return this.request("/auth/verify-code", {
      method: "POST",
      body: JSON.stringify({ email, code })
    });
  }

  async setupPassword(setup_token: string, password: string, confirm_password: string): Promise<{ access_token: string; user: UserSummary }> {
    const res = await this.request<{ access_token: string; user: UserSummary }>("/auth/setup-password", {
      method: "POST",
      body: JSON.stringify({ setup_token, password, confirm_password })
    });
    this.setToken(res.access_token);
    return res;
  }

  async forgotPassword(email: string): Promise<{ message: string }> {
    return this.request("/auth/forgot-password", {
      method: "POST",
      body: JSON.stringify({ email })
    });
  }

  async resetPassword(email: string, reset_code: string, new_password: string, confirm_password: string): Promise<{ message: string }> {
    return this.request("/auth/reset-password", {
      method: "POST",
      body: JSON.stringify({ email, reset_code, new_password, confirm_password })
    });
  }

  async changePassword(current_password: string, new_password: string, confirm_password: string): Promise<{ message: string }> {
    return this.request("/auth/change-password", {
      method: "POST",
      body: JSON.stringify({ current_password, new_password, confirm_password })
    });
  }

  async logout(): Promise<void> {
    try {
      await this.request("/auth/logout", { method: "POST" });
    } catch (e) {
      // Ignore network errors on logout
    }
    this.setToken(null);
  }

  // Auth
  async login(email: string, password: string): Promise<{ access_token: string; user: UserSummary }> {
    const res = await this.request<{ access_token: string; user: UserSummary }>("/auth/login", {
      method: "POST",
      body: JSON.stringify({ email, password })
    });
    this.setToken(res.access_token);
    return res;
  }

  async getMe(): Promise<UserSummary> {
    return this.request<UserSummary>("/auth/me");
  }

  // Admin Management
  async getAuthorizedUsers(): Promise<any[]> {
    return this.request("/admin/authorized-users");
  }

  async addAuthorizedUser(data: { email: string; full_name: string; intended_role: string; student_or_emp_id?: string }): Promise<any> {
    return this.request("/admin/authorized-users", {
      method: "POST",
      body: JSON.stringify(data)
    });
  }

  async getAdminUsers(): Promise<any[]> {
    return this.request("/admin/users");
  }

  async deactivateUser(userId: string): Promise<any> {
    return this.request(`/admin/users/${userId}/deactivate`, { method: "POST" });
  }

  async reactivateUser(userId: string): Promise<any> {
    return this.request(`/admin/users/${userId}/reactivate`, { method: "POST" });
  }

  async unlockUser(userId: string): Promise<any> {
    return this.request(`/admin/users/${userId}/unlock`, { method: "POST" });
  }

  async resendInvitation(userId: string): Promise<any> {
    return this.request(`/admin/users/${userId}/resend-invitation`, { method: "POST" });
  }

  // Curriculum
  async getCurriculumTree(): Promise<Subject[]> {
    return this.request<Subject[]>("/curriculum/tree");
  }

  async updateTopicProgress(topicId: string, status: string, timeSpentSeconds: number): Promise<void> {
    return this.request<void>(`/curriculum/topics/${topicId}/progress`, {
      method: "POST",
      body: JSON.stringify({ status, time_spent_seconds: timeSpentSeconds })
    });
  }

  // MCAT
  async getExams(): Promise<MCATExam[]> {
    return this.request<MCATExam[]>("/mcat/exams");
  }

  async startAttempt(examId: string): Promise<AttemptData> {
    return this.request<AttemptData>("/mcat/attempts/start", {
      method: "POST",
      body: JSON.stringify({ exam_id: examId })
    });
  }

  async saveResponse(
    attemptId: string, 
    questionId: string, 
    selectedOptionId: string | null, 
    isMarkedForReview: boolean, 
    responseTimeSeconds: number
  ): Promise<void> {
    return this.request<void>(`/mcat/attempts/${attemptId}/save-response`, {
      method: "POST",
      body: JSON.stringify({
        question_id: questionId,
        selected_option_id: selectedOptionId,
        is_marked_for_review: isMarkedForReview,
        response_time_seconds: responseTimeSeconds
      })
    });
  }

  async logIntegrityEvent(attemptId: string, eventType: string, severity: string, details?: any): Promise<void> {
    return this.request<void>(`/mcat/attempts/${attemptId}/integrity-event`, {
      method: "POST",
      body: JSON.stringify({
        event_type: eventType,
        severity,
        details
      })
    });
  }

  async submitAttempt(attemptId: string): Promise<ScoreResult> {
    return this.request<ScoreResult>(`/mcat/attempts/${attemptId}/submit`, {
      method: "POST"
    });
  }

  // AROHAN AI
  async getRecommendations(): Promise<Recommendation[]> {
    return this.request<Recommendation[]>("/arohan/recommendations");
  }

  async getCompetencies(): Promise<SkillCompetency[]> {
    return this.request<SkillCompetency[]>("/arohan/competencies");
  }

  async getEvidenceDrawer(skillId: string): Promise<EvidenceDrawerData> {
    return this.request<EvidenceDrawerData>(`/arohan/evidence/${skillId}`);
  }

  // Faculty & Exam Controller
  async getClassSummary(): Promise<any[]> {
    return this.request<any[]>("/faculty/class-summary");
  }

  async createIntervention(studentId: string, skillId: string, notes: string): Promise<void> {
    return this.request<void>("/faculty/interventions", {
      method: "POST",
      body: JSON.stringify({ student_id: studentId, skill_id: skillId, notes })
    });
  }

  async getLiveMonitors(): Promise<LiveMonitorData> {
    return this.request<LiveMonitorData>("/exam-controller/live-monitors");
  }

  async getPlacementReadiness(studentId: string): Promise<any> {
    return this.request<any>(`/placement/readiness/${studentId}`);
  }
}

export const api = new ApiClient();

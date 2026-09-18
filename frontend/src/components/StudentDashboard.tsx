import React, { useEffect, useState } from "react";
import { 
  BookOpen, Brain, Award, Clock, ArrowUpRight, HelpCircle, 
  Calendar, CheckCircle2, ChevronRight, Play, AlertCircle 
} from "lucide-react";
import { api } from "../services/api";
import { Recommendation, SkillCompetency, MCATExam, UserSummary } from "../types";

interface StudentDashboardProps {
  user: UserSummary;
  onOpenEvidence: (skillId: string) => void;
  onStartExam: (examId: string) => void;
  onNavigateTab: (tab: string) => void;
}

export const StudentDashboard: React.FC<StudentDashboardProps> = ({ 
  user, onOpenEvidence, onStartExam, onNavigateTab 
}) => {
  const [recommendations, setRecommendations] = useState<Recommendation[]>([]);
  const [competencies, setCompetencies] = useState<SkillCompetency[]>([]);
  const [exams, setExams] = useState<MCATExam[]>([]);
  const [loading, setLoading] = useState<boolean>(true);

  useEffect(() => {
    Promise.all([
      api.getRecommendations(),
      api.getCompetencies(),
      api.getExams()
    ]).then(([recs, comps, exList]) => {
      setRecommendations(recs);
      setCompetencies(comps);
      setExams(exList);
    }).catch((err) => {
      console.error("Dashboard data load error", err);
    }).finally(() => {
      setLoading(false);
    });
  }, []);

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "clamp(20px, 3vw, 32px)" }}>
      {/* Institutional Greeting Hero */}
      <div className="card" style={{ 
        background: "linear-gradient(135deg, var(--imrd-navy) 0%, var(--imrd-navy-light) 100%)",
        color: "#ffffff",
        padding: "clamp(20px, 4vw, 36px) clamp(16px, 4vw, 40px)",
        border: "none",
        position: "relative",
        overflow: "hidden"
      }}>
        <div style={{ position: "relative", zIndex: 2, maxWidth: 800 }}>
          <div className="brand-badge" style={{ background: "rgba(255, 255, 255, 0.15)", color: "#93c5fd" }}>
            Academic Session 2025-26 • Department of Computer Applications
          </div>
          <h1 style={{ color: "#ffffff", fontSize: "clamp(22px, 4.5vw, 32px)", fontWeight: 800, marginTop: 12, marginBottom: 8 }}>
            Good Morning, {user.first_name} {user.last_name}
          </h1>
          <p style={{ color: "#cbd5e1", fontSize: "clamp(13px, 2vw, 15px)", lineHeight: 1.6 }}>
            Today's Journey is ready. <strong>AROHAN AI</strong> has identified 2 high-yield skill improvements based on your latest empirical assessment evidence.
          </p>

          <div style={{ display: "flex", gap: 12, marginTop: 20, flexWrap: "wrap" }}>
            {exams.length > 0 && (
              <button 
                className="btn btn-gold" 
                onClick={() => onStartExam(exams[0].id)}
              >
                <Play size={16} /> Start MCAT Diagnostic Assessment
              </button>
            )}
            <button 
              className="btn btn-secondary" 
              style={{ background: "rgba(255, 255, 255, 0.1)", color: "#ffffff", borderColor: "rgba(255, 255, 255, 0.25)" }}
              onClick={() => onNavigateTab("curriculum")}
            >
              <BookOpen size={16} /> Explore Curriculum
            </button>
          </div>
        </div>
      </div>

      {/* Top Stat Metrics */}
      <div className="grid-4">
        <div className="card">
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 12 }}>
            <span style={{ fontSize: 13, color: "var(--text-muted)", fontWeight: 600 }}>Curriculum Enrolled</span>
            <BookOpen size={18} color="var(--imrd-blue)" />
          </div>
          <div style={{ fontSize: "clamp(22px, 3.5vw, 28px)", fontWeight: 800 }}>3 Subjects</div>
          <div style={{ fontSize: 12, color: "var(--imrd-emerald)", marginTop: 4, display: "flex", alignItems: "center", gap: 4 }}>
            <CheckCircle2 size={12} /> BCA Semester 3 Active
          </div>
        </div>

        <div className="card">
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 12 }}>
            <span style={{ fontSize: 13, color: "var(--text-muted)", fontWeight: 600 }}>Skills Evaluated</span>
            <Brain size={18} color="var(--imrd-blue)" />
          </div>
          <div style={{ fontSize: "clamp(22px, 3.5vw, 28px)", fontWeight: 800 }}>{competencies.length} Skills</div>
          <div style={{ fontSize: 12, color: "var(--text-muted)", marginTop: 4 }}>
            Bayesian Knowledge Tracing
          </div>
        </div>

        <div className="card">
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 12 }}>
            <span style={{ fontSize: 13, color: "var(--text-muted)", fontWeight: 600 }}>MCAT Aptitude Level</span>
            <Award size={18} color="var(--imrd-gold)" />
          </div>
          <div style={{ fontSize: "clamp(22px, 3.5vw, 28px)", fontWeight: 800, color: "var(--imrd-gold)" }}>Diagnostic</div>
          <div style={{ fontSize: 12, color: "var(--text-muted)", marginTop: 4 }}>
            Modular Computerized Aptitude
          </div>
        </div>

        <div className="card">
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 12 }}>
            <span style={{ fontSize: 13, color: "var(--text-muted)", fontWeight: 600 }}>Placement Readiness</span>
            <ArrowUpRight size={18} color="var(--imrd-emerald)" />
          </div>
          <div style={{ fontSize: "clamp(22px, 3.5vw, 28px)", fontWeight: 800, color: "var(--imrd-emerald)" }}>80.7%</div>
          <div style={{ fontSize: 12, color: "var(--text-muted)", marginTop: 4 }}>
            Verified Evidence Index
          </div>
        </div>
      </div>

      {/* Main Grid: AROHAN Recommendations + Today's Schedule */}
      <div className="responsive-grid-2-1">
        {/* Left: AROHAN AI Recommendations with Evidence Drawers */}
        <div style={{ display: "flex", flexDirection: "column", gap: 20, minWidth: 0 }}>
          <div className="card">
            <div className="card-header">
              <div>
                <span className="badge badge-blue">Adaptive Intelligence Layer</span>
                <h2 className="card-title" style={{ marginTop: 6 }}>
                  <Brain size={20} color="var(--imrd-blue)" /> AROHAN Recommended Actions
                </h2>
              </div>
              <span style={{ fontSize: 12, color: "var(--text-muted)" }}>Strict Evidence-Based</span>
            </div>

            {recommendations.length === 0 ? (
              <div style={{ textAlign: "center", padding: "40px 0", color: "var(--text-muted)" }}>
                No immediate skill gaps detected. You are keeping up with syllabus benchmarks!
              </div>
            ) : (
              <div style={{ display: "flex", flexDirection: "column", gap: 16 }}>
                {recommendations.map((rec) => (
                  <div 
                    key={rec.id}
                    style={{
                      border: "1px solid var(--border-subtle)",
                      borderRadius: "var(--radius-md)",
                      padding: "clamp(14px, 2.5vw, 18px)",
                      background: "var(--surface-hover)",
                      transition: "all 0.15s ease"
                    }}
                  >
                    <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", flexWrap: "wrap", gap: 12 }}>
                      <div style={{ flex: "1 1 240px", minWidth: 0 }}>
                        <span className="badge badge-ruby" style={{ marginBottom: 6 }}>
                          {rec.action_type === "PREREQUISITE_LEARN" ? "Foundational Gap" : "Targeted Practice"}
                        </span>
                        <h4 style={{ fontSize: 16, fontWeight: 700, marginTop: 4, overflowWrap: "anywhere" }}>{rec.title}</h4>
                        <p style={{ fontSize: 13, color: "var(--text-secondary)", marginTop: 4, lineHeight: 1.5 }}>
                          {rec.evidence_summary}
                        </p>
                      </div>

                      <button
                        className="btn btn-secondary"
                        style={{ fontSize: 12, padding: "6px 12px" }}
                        onClick={() => onOpenEvidence(rec.skill_id)}
                      >
                        <HelpCircle size={14} /> Why am I seeing this?
                      </button>
                    </div>

                    <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginTop: 14, paddingTop: 12, borderTop: "1px solid var(--border-subtle)", fontSize: 12, flexWrap: "wrap", gap: 10 }}>
                      <span style={{ color: "var(--text-muted)" }}>Target Skill: <strong>{rec.skill_name}</strong></span>
                      <button 
                        className="btn btn-primary"
                        style={{ fontSize: 12, padding: "6px 14px" }}
                        onClick={() => {
                          if (exams.length > 0) onStartExam(exams[0].id);
                        }}
                      >
                        Start Learning Action <ChevronRight size={14} />
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Skill Competency Matrix */}
          <div className="card">
            <div className="card-header">
              <h2 className="card-title">
                <Award size={20} color="var(--imrd-navy)" /> Student Competency Matrix
              </h2>
              <span style={{ fontSize: 12, color: "var(--text-muted)" }}>Posterior Probability P(L)</span>
            </div>

            <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
              {competencies.map((comp) => {
                const pct = Math.round(comp.mastery_probability * 100);
                const isWeak = comp.mastery_probability < 0.50;
                return (
                  <div key={comp.skill_id} style={{ display: "flex", alignItems: "center", justifyContent: "space-between", padding: "10px 14px", background: "var(--surface-hover)", borderRadius: "var(--radius-sm)", flexWrap: "wrap", gap: 10 }}>
                    <div style={{ flex: "1 1 180px", minWidth: 0 }}>
                      <div style={{ fontWeight: 600, fontSize: 14 }}>{comp.skill_name}</div>
                      <div style={{ fontSize: 11, color: "var(--text-muted)" }}>{comp.category} • {comp.evidence_count} signals</div>
                    </div>

                    <div style={{ flex: "2 1 160px", minWidth: 120 }}>
                      <div style={{ height: 8, background: "var(--border-subtle)", borderRadius: 999, overflow: "hidden" }}>
                        <div 
                          style={{ 
                            height: "100%", 
                            width: `${pct}%`, 
                            background: isWeak ? "var(--imrd-ruby)" : "var(--imrd-emerald)",
                            borderRadius: 999
                          }} 
                        />
                      </div>
                    </div>

                    <div style={{ textAlign: "right", flexShrink: 0 }}>
                      <span className={`badge ${isWeak ? "badge-ruby" : "badge-emerald"}`}>
                        {comp.status_label}
                      </span>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        </div>

        {/* Right Col: Today's Academic Schedule & Announcements */}
        <div style={{ display: "flex", flexDirection: "column", gap: 20 }}>
          <div className="card">
            <div className="card-header">
              <h3 className="card-title" style={{ fontSize: 16 }}>
                <Calendar size={18} color="var(--imrd-blue)" /> Today's Lecture Schedule
              </h3>
            </div>

            <div style={{ display: "flex", flexDirection: "column", gap: 14 }}>
              <div style={{ borderLeft: "3px solid var(--imrd-blue)", paddingLeft: 12 }}>
                <div style={{ fontSize: 11, color: "var(--imrd-blue)", fontWeight: 700 }}>10:30 AM - 11:30 AM</div>
                <div style={{ fontWeight: 600, fontSize: 14 }}>Data Structures & Algorithms</div>
                <div style={{ fontSize: 12, color: "var(--text-muted)" }}>Prof. S. N. Patil • Lab 2</div>
              </div>

              <div style={{ borderLeft: "3px solid var(--imrd-gold)", paddingLeft: 12 }}>
                <div style={{ fontSize: 11, color: "var(--imrd-gold)", fontWeight: 700 }}>11:45 AM - 12:45 PM</div>
                <div style={{ fontWeight: 600, fontSize: 14 }}>Quantitative Aptitude (MCAT Prep)</div>
                <div style={{ fontSize: 12, color: "var(--text-muted)" }}>Dr. V. A. Pawar • Room 204</div>
              </div>

              <div style={{ borderLeft: "3px solid var(--imrd-emerald)", paddingLeft: 12 }}>
                <div style={{ fontSize: 11, color: "var(--imrd-emerald)", fontWeight: 700 }}>02:00 PM - 04:00 PM</div>
                <div style={{ fontWeight: 600, fontSize: 14 }}>Java Programming Practical Lab</div>
                <div style={{ fontSize: 12, color: "var(--text-muted)" }}>Software Lab 1</div>
              </div>
            </div>
          </div>

          <div className="card" style={{ background: "var(--imrd-gold-light)", border: "1px solid #fde68a" }}>
            <h4 style={{ fontSize: 14, color: "var(--imrd-gold)", marginBottom: 8, display: "flex", alignItems: "center", gap: 6 }}>
              <AlertCircle size={16} /> Institutional Circular
            </h4>
            <p style={{ fontSize: 13, color: "#78350f", lineHeight: 1.5 }}>
              Upcoming MCAT Aptitude Assessment drive commences next week for all BCA & MCA candidates. Ensure diagnostic benchmarks are completed.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

import React, { useEffect, useState } from "react";
import { Users, AlertTriangle, CheckCircle2, UserCheck, ShieldAlert, Send } from "lucide-react";
import { api } from "../services/api";

export const FacultyPortal: React.FC = () => {
  const [summary, setSummary] = useState<any[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [notes, setNotes] = useState<string>("");
  const [selectedSkill, setSelectedSkill] = useState<any | null>(null);
  const [assignedMessage, setAssignedMessage] = useState<string | null>(null);

  useEffect(() => {
    api.getClassSummary().then((res) => {
      setSummary(res);
    }).finally(() => setLoading(false));
  }, []);

  const handleAssignIntervention = async () => {
    if (!selectedSkill || !notes.trim()) return;
    try {
      await api.createIntervention("u-student1", selectedSkill.skill_id, notes);
      setAssignedMessage(`Remedial intervention assigned for ${selectedSkill.skill_name}!`);
      setNotes("");
      setSelectedSkill(null);
      setTimeout(() => setAssignedMessage(null), 4000);
    } catch (err: any) {
      alert(`Error: ${err.message}`);
    }
  };

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 24 }}>
      <div className="card-header">
        <div>
          <span className="badge badge-blue">Faculty Guidance Console</span>
          <h1 style={{ fontSize: "clamp(20px, 4vw, 26px)", marginTop: 4 }}>Departmental Concept Mastery & Student Interventions</h1>
        </div>
        <div style={{ fontSize: 13, color: "var(--text-muted)" }}>
          Philosophy: "AI Recommends. Faculty Guides. Student Improves."
        </div>
      </div>

      {assignedMessage && (
        <div style={{ background: "var(--imrd-emerald-light)", color: "var(--imrd-emerald)", padding: "12px 20px", borderRadius: "var(--radius-md)", border: "1px solid var(--imrd-emerald-border)", display: "flex", alignItems: "center", gap: 8, flexWrap: "wrap" }}>
          <CheckCircle2 size={18} /> {assignedMessage}
        </div>
      )}

      <div className="responsive-grid-2-1">
        {/* Class Skill Matrix Table */}
        <div className="card">
          <h3 style={{ fontSize: 16, marginBottom: 16, display: "flex", alignItems: "center", gap: 8 }}>
            <Users size={18} color="var(--imrd-blue)" /> Class Concept Mastery Distribution
          </h3>

          <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
            {summary.map((sk) => (
              <div 
                key={sk.skill_id}
                style={{
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "space-between",
                  padding: "clamp(12px, 2.5vw, 16px)",
                  borderRadius: "var(--radius-md)",
                  border: sk.remedial_flag ? "1px solid var(--imrd-ruby-border)" : "1px solid var(--border-subtle)",
                  background: sk.remedial_flag ? "var(--imrd-ruby-light)" : "var(--surface-white)",
                  flexWrap: "wrap",
                  gap: 12
                }}
              >
                <div style={{ flex: "1 1 220px", minWidth: 0 }}>
                  <div style={{ display: "flex", alignItems: "center", gap: 8, flexWrap: "wrap" }}>
                    <span style={{ fontWeight: 700, fontSize: 15 }}>{sk.skill_name}</span>
                    <span className="badge badge-blue">{sk.category}</span>
                    {sk.remedial_flag && (
                      <span className="badge badge-ruby" style={{ display: "flex", alignItems: "center", gap: 4 }}>
                        <AlertTriangle size={12} /> Concept Gap Cluster
                      </span>
                    )}
                  </div>
                  <div style={{ fontSize: 12, color: "var(--text-muted)", marginTop: 4 }}>
                    Assessed Candidates: {sk.assessed_students}
                  </div>
                </div>

                <div style={{ display: "flex", alignItems: "center", gap: "clamp(10px, 2vw, 20px)", flexWrap: "wrap" }}>
                  <div style={{ textAlign: "right" }}>
                    <div style={{ fontSize: 20, fontWeight: 800, color: sk.remedial_flag ? "var(--imrd-ruby)" : "var(--imrd-emerald)" }}>
                      {Math.round(sk.average_mastery * 100)}%
                    </div>
                    <div style={{ fontSize: 11, color: "var(--text-muted)" }}>Class Avg P(L)</div>
                  </div>

                  <button
                    className="btn btn-secondary"
                    style={{ fontSize: 12, padding: "6px 12px" }}
                    onClick={() => setSelectedSkill(sk)}
                  >
                    Intervene
                  </button>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Remedial Intervention Drawer */}
        <div className="card">
          <h3 style={{ fontSize: 16, marginBottom: 16, display: "flex", alignItems: "center", gap: 8 }}>
            <UserCheck size={18} color="var(--imrd-navy)" /> Assign Faculty Intervention
          </h3>

          {selectedSkill ? (
            <div style={{ display: "flex", flexDirection: "column", gap: 14 }}>
              <div style={{ background: "var(--surface-hover)", padding: 12, borderRadius: "var(--radius-sm)" }}>
                <div style={{ fontSize: 12, color: "var(--text-muted)" }}>Selected Target Concept:</div>
                <div style={{ fontWeight: 700, fontSize: 16 }}>{selectedSkill.skill_name}</div>
                <div style={{ fontSize: 12, color: "var(--imrd-ruby)", fontWeight: 600 }}>
                  Class Mastery: {Math.round(selectedSkill.average_mastery * 100)}%
                </div>
              </div>

              <div>
                <label style={{ fontSize: 13, fontWeight: 600, display: "block", marginBottom: 6 }}>
                  Faculty Remedial Instructions / Problem Set:
                </label>
                <textarea
                  rows={4}
                  value={notes}
                  onChange={(e) => setNotes(e.target.value)}
                  placeholder="e.g. Schedule laboratory problem-solving session on percentage multipliers and fraction conversion table."
                  style={{
                    width: "100%",
                    padding: 10,
                    borderRadius: "var(--radius-sm)",
                    border: "1px solid var(--border-strong)",
                    fontFamily: "inherit",
                    fontSize: 13
                  }}
                />
              </div>

              <button className="btn btn-navy" onClick={handleAssignIntervention}>
                <Send size={14} /> Commit Intervention to Student
              </button>
            </div>
          ) : (
            <div style={{ textAlign: "center", padding: "40px 0", color: "var(--text-muted)", fontSize: 13 }}>
              Select a concept from the left panel to assign guided remedial practice or notes to struggling candidates.
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

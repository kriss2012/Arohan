import React, { useEffect, useState } from "react";
import { X, Brain, CheckCircle2, XCircle, Calculator, ShieldCheck, Activity } from "lucide-react";
import { api } from "../services/api";
import { EvidenceDrawerData } from "../types";

interface EvidenceDrawerProps {
  skillId: string | null;
  onClose: () => void;
}

export const EvidenceDrawer: React.FC<EvidenceDrawerProps> = ({ skillId, onClose }) => {
  const [data, setData] = useState<EvidenceDrawerData | null>(null);
  const [loading, setLoading] = useState<boolean>(true);

  useEffect(() => {
    if (!skillId) return;
    setLoading(true);
    api.getEvidenceDrawer(skillId)
      .then((res) => setData(res))
      .catch((err) => console.error("Error loading evidence drawer", err))
      .finally(() => setLoading(false));
  }, [skillId]);

  if (!skillId) return null;

  return (
    <div className="drawer-backdrop" onClick={onClose}>
      <div className="drawer-panel" onClick={(e) => e.stopPropagation()}>
        <div className="drawer-header">
          <div>
            <div style={{ display: "flex", alignItems: "center", gap: 8, fontSize: 12, color: "#93c5fd", textTransform: "uppercase", letterSpacing: "0.05em" }}>
              <Brain size={14} /> AROHAN AI Intelligence
            </div>
            <h3 style={{ color: "#ffffff", marginTop: 4 }}>Why Am I Seeing This?</h3>
          </div>
          <button 
            onClick={onClose}
            style={{ background: "transparent", border: "none", color: "#ffffff", cursor: "pointer" }}
          >
            <X size={22} />
          </button>
        </div>

        <div className="drawer-body">
          {loading ? (
            <div style={{ textAlign: "center", padding: "60px 0", color: "var(--text-muted)" }}>
              Retrieving Bayesian student evidence...
            </div>
          ) : !data ? (
            <div style={{ textAlign: "center", padding: "40px 0" }}>No evidence found for this skill.</div>
          ) : (
            <>
              {/* Skill & Mastery Card */}
              <div className="card" style={{ background: "var(--surface-hover)" }}>
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start" }}>
                  <div>
                    <span className="badge badge-blue">{data.category}</span>
                    <h2 style={{ fontSize: 20, marginTop: 8 }}>{data.skill_name}</h2>
                  </div>
                  <div style={{ textAlign: "right" }}>
                    <div style={{ fontSize: 24, fontWeight: 800, color: data.mastery_probability < 0.5 ? "var(--imrd-ruby)" : "var(--imrd-blue)" }}>
                      {Math.round(data.mastery_probability * 100)}%
                    </div>
                    <div style={{ fontSize: 11, color: "var(--text-muted)" }}>Bayesian Mastery P(L)</div>
                  </div>
                </div>

                <div style={{ marginTop: 16 }}>
                  <div style={{ display: "flex", justifyContent: "space-between", fontSize: 12, marginBottom: 6 }}>
                    <span style={{ color: "var(--text-secondary)" }}>Statistical Confidence</span>
                    <span style={{ fontWeight: 600 }}>{Math.round(data.confidence_score * 100)}%</span>
                  </div>
                  <div style={{ height: 6, background: "var(--border-subtle)", borderRadius: 999, overflow: "hidden" }}>
                    <div 
                      style={{ 
                        height: "100%", 
                        width: `${Math.round(data.confidence_score * 100)}%`, 
                        background: "var(--imrd-blue)",
                        borderRadius: 999 
                      }} 
                    />
                  </div>
                </div>
              </div>

              {/* Assessment Evidence Breakdown */}
              <div className="card">
                <h4 style={{ fontSize: 15, marginBottom: 14, display: "flex", alignItems: "center", gap: 8 }}>
                  <ShieldCheck size={18} color="var(--imrd-blue)" /> Empirical Response History
                </h4>
                <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(130px, 1fr))", gap: 12 }}>
                  <div style={{ background: "var(--imrd-emerald-light)", border: "1px solid var(--imrd-emerald-border)", padding: 12, borderRadius: "var(--radius-md)", display: "flex", alignItems: "center", gap: 10 }}>
                    <CheckCircle2 color="var(--imrd-emerald)" size={24} />
                    <div>
                      <div style={{ fontSize: 18, fontWeight: 700, color: "var(--imrd-emerald)" }}>{data.correct_count}</div>
                      <div style={{ fontSize: 11, color: "var(--text-secondary)" }}>Correct Answers</div>
                    </div>
                  </div>
                  <div style={{ background: "var(--imrd-ruby-light)", border: "1px solid var(--imrd-ruby-border)", padding: 12, borderRadius: "var(--radius-md)", display: "flex", alignItems: "center", gap: 10 }}>
                    <XCircle color="var(--imrd-ruby)" size={24} />
                    <div>
                      <div style={{ fontSize: 18, fontWeight: 700, color: "var(--imrd-ruby)" }}>{data.incorrect_count}</div>
                      <div style={{ fontSize: 11, color: "var(--text-secondary)" }}>Incorrect Answers</div>
                    </div>
                  </div>
                </div>
              </div>

              {/* Mathematical Rationale */}
              <div className="card" style={{ borderLeft: "4px solid var(--imrd-blue)" }}>
                <h4 style={{ fontSize: 14, marginBottom: 8, display: "flex", alignItems: "center", gap: 8 }}>
                  <Calculator size={16} color="var(--imrd-blue)" /> Multi-Factor Gap Formulation
                </h4>
                <p style={{ fontSize: 13, color: "var(--text-secondary)", lineHeight: 1.6 }}>
                  {data.recommendation_logic}
                </p>
                <div style={{ marginTop: 12, background: "var(--bg-slate)", padding: 10, borderRadius: "var(--radius-sm)", fontSize: 12, color: "var(--text-muted)", fontFamily: "monospace", overflowWrap: "anywhere" }}>
                  GapScore = 0.45 * (1 - P(L)) + 0.20 * ErrorRate = {data.gap_score.toFixed(3)}
                </div>
              </div>

              {/* Event Stream */}
              <div>
                <h4 style={{ fontSize: 14, marginBottom: 12, display: "flex", alignItems: "center", gap: 8, color: "var(--text-muted)" }}>
                  <Activity size={16} /> Recent Immutable Events
                </h4>
                <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
                  {data.recent_evidence_events.map((ev, idx) => (
                    <div key={idx} style={{ fontSize: 12, padding: "8px 12px", background: "var(--surface-white)", border: "1px solid var(--border-subtle)", borderRadius: "var(--radius-sm)", display: "flex", justifyContent: "space-between" }}>
                      <span style={{ fontWeight: 600 }}>{ev.event_type}</span>
                      <span style={{ color: "var(--text-muted)" }}>{ev.source}</span>
                    </div>
                  ))}
                </div>
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  );
};

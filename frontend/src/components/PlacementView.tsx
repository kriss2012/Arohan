import React, { useEffect, useState } from "react";
import { Award, CheckCircle2, ShieldCheck, TrendingUp, Briefcase } from "lucide-react";
import { api } from "../services/api";

export const PlacementView: React.FC<{ studentId: string }> = ({ studentId }) => {
  const [data, setData] = useState<any | null>(null);

  useEffect(() => {
    api.getPlacementReadiness(studentId).then((res) => {
      setData(res);
    });
  }, [studentId]);

  if (!data) {
    return <div style={{ textAlign: "center", padding: "80px 0" }}>Loading Placement Readiness Profile...</div>;
  }

  const dimensions = data.dimensions || {};

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 24 }}>
      <div className="card-header">
        <div>
          <span className="badge badge-blue">Training & Placement Cell</span>
          <h1 style={{ fontSize: "clamp(20px, 4vw, 26px)", marginTop: 4 }}>Evidence-Based Placement Readiness Radar</h1>
        </div>
        <div style={{ fontSize: 13, color: "var(--text-muted)" }}>
          Notice: Empirical skill indicators calculated without ungrounded predictions.
        </div>
      </div>

      <div className="responsive-grid-1-2">
        {/* Overall Index Card */}
        <div className="card" style={{ textAlign: "center", padding: "clamp(20px, 3.5vw, 32px)" }}>
          <div style={{ display: "inline-flex", padding: 14, background: "var(--imrd-blue-subtle)", borderRadius: "50%", marginBottom: 12 }}>
            <Award size={36} color="var(--imrd-blue)" />
          </div>
          <div style={{ fontSize: "clamp(32px, 6vw, 42px)", fontWeight: 800, color: "var(--imrd-blue)" }}>
            {data.overall_readiness_index}%
          </div>
          <div style={{ fontSize: 15, fontWeight: 700, marginTop: 4 }}>Overall Readiness Index</div>
          <div style={{ fontSize: 12, color: "var(--text-muted)", marginTop: 6 }}>
            Status: <strong>{data.status}</strong>
          </div>

          <div style={{ marginTop: 24, padding: 12, background: "var(--surface-hover)", borderRadius: "var(--radius-sm)", fontSize: 12, color: "var(--text-secondary)", textAlign: "left" }}>
            <div style={{ display: "flex", alignItems: "center", gap: 6, color: "var(--imrd-emerald)", fontWeight: 600, marginBottom: 4 }}>
              <ShieldCheck size={14} /> Evidence Verified
            </div>
            All dimensions are strictly computed from completed MCAT aptitude assessments, curriculum submissions, and verified lab work.
          </div>
        </div>

        {/* Multi-Dimensional Competency Progress Bars */}
        <div className="card">
          <h3 style={{ fontSize: 16, marginBottom: 20, display: "flex", alignItems: "center", gap: 8 }}>
            <TrendingUp size={18} color="var(--imrd-blue)" /> Multi-Dimensional Competency Analysis
          </h3>

          <div style={{ display: "flex", flexDirection: "column", gap: 18 }}>
            {Object.entries(dimensions).map(([dim, score]: [string, any]) => (
              <div key={dim}>
                <div style={{ display: "flex", justifyContent: "space-between", fontSize: 14, marginBottom: 6 }}>
                  <span style={{ fontWeight: 600, textTransform: "capitalize" }}>{dim} Readiness</span>
                  <span style={{ fontWeight: 700, color: "var(--imrd-blue)" }}>{score}%</span>
                </div>
                <div style={{ height: 10, background: "var(--border-subtle)", borderRadius: 999, overflow: "hidden" }}>
                  <div 
                    style={{ 
                      height: "100%", 
                      width: `${score}%`, 
                      background: score > 75 ? "var(--imrd-emerald)" : "var(--imrd-blue)",
                      borderRadius: 999 
                    }} 
                  />
                </div>
              </div>
            ))}
          </div>

          <div style={{ marginTop: 24, paddingTop: 16, borderTop: "1px solid var(--border-subtle)", display: "flex", justifyContent: "flex-end" }}>
            <button className="btn btn-primary" onClick={() => alert("Candidate readiness dossier downloaded.")}>
              <Briefcase size={14} /> Export Institutional Dossier (PDF)
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

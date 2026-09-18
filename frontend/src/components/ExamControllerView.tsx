import React, { useEffect, useState } from "react";
import { Activity, ShieldAlert, CheckCircle, Clock, Users, RefreshCw } from "lucide-react";
import { api } from "../services/api";
import { LiveMonitorData } from "../types";

export const ExamControllerView: React.FC = () => {
  const [data, setData] = useState<LiveMonitorData | null>(null);
  const [loading, setLoading] = useState<boolean>(true);

  const fetchLive = () => {
    setLoading(true);
    api.getLiveMonitors()
      .then((res) => setData(res))
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    fetchLive();
    const interval = setInterval(fetchLive, 6000);
    return () => clearInterval(interval);
  }, []);

  if (loading && !data) {
    return <div style={{ textAlign: "center", padding: "80px 0" }}>Connecting to Live Examination Server...</div>;
  }

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 24 }}>
      <div className="card-header">
        <div>
          <span className="badge badge-ruby">Live Examination Console</span>
          <h1 style={{ fontSize: "clamp(20px, 4vw, 26px)", marginTop: 4 }}>Active Examination Room & Integrity Signal Monitor</h1>
        </div>
        <button className="btn btn-secondary" onClick={fetchLive}>
          <RefreshCw size={14} /> Refresh Live Stream
        </button>
      </div>

      {/* Overview Stat Metrics */}
      <div className="grid-4">
        <div className="card">
          <span style={{ fontSize: 12, color: "var(--text-muted)" }}>Total Active Candidates</span>
          <div style={{ fontSize: "clamp(22px, 3.5vw, 28px)", fontWeight: 800, color: "var(--imrd-navy)", marginTop: 4 }}>
            {data?.active_candidates_count || 0}
          </div>
        </div>

        <div className="card">
          <span style={{ fontSize: 12, color: "var(--text-muted)" }}>Completed Submissions</span>
          <div style={{ fontSize: "clamp(22px, 3.5vw, 28px)", fontWeight: 800, color: "var(--imrd-emerald)", marginTop: 4 }}>
            {data?.status_distribution["AUTO_EVALUATED"] || 0}
          </div>
        </div>

        <div className="card">
          <span style={{ fontSize: 12, color: "var(--text-muted)" }}>In-Progress / Kiosk Active</span>
          <div style={{ fontSize: "clamp(22px, 3.5vw, 28px)", fontWeight: 800, color: "var(--imrd-blue)", marginTop: 4 }}>
            {data?.status_distribution["STARTED"] || 0}
          </div>
        </div>

        <div className="card">
          <span style={{ fontSize: 12, color: "var(--text-muted)" }}>Integrity Signals Logged</span>
          <div style={{ fontSize: "clamp(22px, 3.5vw, 28px)", fontWeight: 800, color: "var(--imrd-gold)", marginTop: 4 }}>
            {(data?.integrity_signal_severity["LOW"] || 0) + (data?.integrity_signal_severity["MEDIUM"] || 0)}
          </div>
        </div>
      </div>

      {/* Candidate Sessions Table */}
      <div className="card">
        <h3 style={{ fontSize: 16, marginBottom: 16, display: "flex", alignItems: "center", gap: 8 }}>
          <Users size={18} color="var(--imrd-blue)" /> Candidate Live Session Stream
        </h3>

        <div className="responsive-table-container">
          <table style={{ width: "100%", minWidth: "620px", borderCollapse: "collapse", fontSize: 13, textAlign: "left" }}>
            <thead>
              <tr style={{ borderBottom: "2px solid var(--border-subtle)", color: "var(--text-muted)" }}>
                <th style={{ padding: 12 }}>Candidate Name</th>
                <th style={{ padding: 12 }}>Email / ID</th>
                <th style={{ padding: 12 }}>Session Status</th>
                <th style={{ padding: 12 }}>Score %</th>
                <th style={{ padding: 12 }}>Integrity Signals</th>
              </tr>
            </thead>
            <tbody>
              {data?.candidates.map((cand) => (
                <tr key={cand.attempt_id} style={{ borderBottom: "1px solid var(--border-subtle)" }}>
                  <td style={{ padding: 12, fontWeight: 600 }}>{cand.student_name}</td>
                  <td style={{ padding: 12, color: "var(--text-secondary)" }}>{cand.student_email}</td>
                  <td style={{ padding: 12 }}>
                    <span className={`badge ${cand.status === "AUTO_EVALUATED" ? "badge-emerald" : "badge-blue"}`}>
                      {cand.status}
                    </span>
                  </td>
                  <td style={{ padding: 12, fontWeight: 700 }}>
                    {cand.status === "AUTO_EVALUATED" ? `${cand.score_percentage}%` : "--"}
                  </td>
                  <td style={{ padding: 12 }}>
                    <span className={`badge ${cand.integrity_signal_count > 0 ? "badge-gold" : "badge-emerald"}`}>
                      {cand.integrity_signal_count} signals
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Real-time Environmental Signals Audit Log */}
      <div className="card">
        <h3 style={{ fontSize: 16, marginBottom: 16, display: "flex", alignItems: "center", gap: 8 }}>
          <ShieldAlert size={18} color="var(--imrd-ruby)" /> Real-Time Integrity Signals Audit Feed
        </h3>

        <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
          {data?.recent_integrity_signals.map((sig) => (
            <div
              key={sig.id}
              style={{
                display: "flex",
                alignItems: "center",
                justifyContent: "space-between",
                padding: "10px 14px",
                background: "var(--surface-hover)",
                borderRadius: "var(--radius-sm)",
                borderLeft: sig.severity === "HIGH" ? "3px solid var(--imrd-ruby)" : "3px solid var(--imrd-gold)"
              }}
            >
              <div>
                <span className={`badge ${sig.severity === "HIGH" ? "badge-ruby" : "badge-gold"}`}>
                  {sig.severity} Severity
                </span>
                <span style={{ fontWeight: 600, fontSize: 13, marginLeft: 10 }}>{sig.event_type}</span>
                <span style={{ fontSize: 12, color: "var(--text-secondary)", marginLeft: 12 }}>{sig.details}</span>
              </div>

              <div style={{ fontSize: 11, color: "var(--text-muted)", fontFamily: "monospace" }}>
                {new Date(sig.timestamp).toLocaleTimeString()}
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

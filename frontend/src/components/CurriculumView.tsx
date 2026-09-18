import React, { useEffect, useState } from "react";
import { BookOpen, CheckCircle, FileText, ChevronDown, ChevronRight, Clock, Award } from "lucide-react";
import { api } from "../services/api";
import { Subject, Topic } from "../types";

export const CurriculumView: React.FC = () => {
  const [subjects, setSubjects] = useState<Subject[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [selectedTopic, setSelectedTopic] = useState<Topic | null>(null);
  const [completedTopicIds, setCompletedTopicIds] = useState<Set<string>>(new Set());

  useEffect(() => {
    api.getCurriculumTree()
      .then((subs) => {
        setSubjects(subs);
        if (subs.length > 0 && subs[0].units.length > 0 && subs[0].units[0].topics.length > 0) {
          setSelectedTopic(subs[0].units[0].topics[0]);
        }
      })
      .finally(() => setLoading(false));
  }, []);

  const handleMarkComplete = async (topic: Topic) => {
    await api.updateTopicProgress(topic.id, "COMPLETED", 300);
    setCompletedTopicIds((prev) => new Set([...prev, topic.id]));
  };

  if (loading) {
    return <div style={{ textAlign: "center", padding: "80px 0" }}>Loading academic syllabus tree...</div>;
  }

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 24 }}>
      <div className="card-header">
        <div>
          <span className="badge badge-blue">Academic Curriculum</span>
          <h1 style={{ fontSize: "clamp(20px, 4vw, 26px)", marginTop: 4 }}>BCA Semester III: Syllabus & Learning Materials</h1>
        </div>
        <div style={{ fontSize: 13, color: "var(--text-muted)" }}>
          Institute of Management Research and Development, Shirpur
        </div>
      </div>

      <div className="responsive-grid-sidebar">
        {/* Left: Hierarchical Tree */}
        <div className="card" style={{ padding: "clamp(14px, 2.5vw, 18px)" }}>
          <h3 style={{ fontSize: 15, marginBottom: 16, display: "flex", alignItems: "center", gap: 8 }}>
            <BookOpen size={18} color="var(--imrd-blue)" /> Program Structure
          </h3>

          <div style={{ display: "flex", flexDirection: "column", gap: 14 }}>
            {subjects.map((sub) => (
              <div key={sub.id} style={{ borderBottom: "1px solid var(--border-subtle)", paddingBottom: 12 }}>
                <div style={{ fontWeight: 700, fontSize: 14, color: "var(--imrd-navy)", marginBottom: 6 }}>
                  {sub.name} ({sub.code})
                </div>

                <div style={{ display: "flex", flexDirection: "column", gap: 6, paddingLeft: 8 }}>
                  {sub.units.map((unit) => (
                    <div key={unit.id}>
                      <div style={{ fontSize: 12, fontWeight: 600, color: "var(--text-secondary)", margin: "4px 0" }}>
                        Unit {unit.unit_number}: {unit.title}
                      </div>

                      <div style={{ display: "flex", flexDirection: "column", gap: 3, paddingLeft: 10 }}>
                        {unit.topics.map((top) => {
                          const isSelected = selectedTopic?.id === top.id;
                          const isDone = completedTopicIds.has(top.id);
                          return (
                            <button
                              key={top.id}
                              onClick={() => setSelectedTopic(top)}
                              style={{
                                display: "flex",
                                alignItems: "center",
                                justifyContent: "space-between",
                                gap: 8,
                                padding: "8px 10px",
                                borderRadius: "var(--radius-sm)",
                                border: "none",
                                background: isSelected ? "var(--imrd-blue-subtle)" : "transparent",
                                color: isSelected ? "var(--imrd-blue)" : "var(--text-primary)",
                                fontWeight: isSelected ? 600 : 400,
                                fontSize: 13,
                                textAlign: "left",
                                cursor: "pointer",
                                wordBreak: "break-word"
                              }}
                            >
                              <span>{top.title}</span>
                              {isDone && <CheckCircle size={14} color="var(--imrd-emerald)" style={{ flexShrink: 0 }} />}
                            </button>
                          );
                        })}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Right: Topic Reading View */}
        <div className="card">
          {selectedTopic ? (
            <div>
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: 16, flexWrap: "wrap", gap: 12 }}>
                <div style={{ flex: "1 1 240px", minWidth: 0 }}>
                  <span className="badge badge-blue">Academic Learning Objective</span>
                  <h2 style={{ fontSize: "clamp(18px, 3.5vw, 22px)", marginTop: 8 }}>{selectedTopic.title}</h2>
                  <p style={{ color: "var(--text-secondary)", fontSize: 14, marginTop: 6, lineHeight: 1.6 }}>
                    {selectedTopic.learning_objective}
                  </p>
                </div>

                <button
                  className={`btn ${completedTopicIds.has(selectedTopic.id) ? "btn-secondary" : "btn-primary"}`}
                  onClick={() => handleMarkComplete(selectedTopic)}
                >
                  <CheckCircle size={16} /> {completedTopicIds.has(selectedTopic.id) ? "Marked Complete" : "Mark as Completed"}
                </button>
              </div>

              {/* Resource Content */}
              <div style={{ marginTop: 24 }}>
                <h4 style={{ fontSize: 16, marginBottom: 12, display: "flex", alignItems: "center", gap: 8 }}>
                  <FileText size={18} color="var(--imrd-blue)" /> Institutional Course Notes
                </h4>

                {selectedTopic.resources.length > 0 ? (
                  <div style={{ background: "var(--bg-slate)", padding: 24, borderRadius: "var(--radius-md)", border: "1px solid var(--border-subtle)" }}>
                    <div style={{ fontWeight: 700, fontSize: 16, marginBottom: 8 }}>
                      {selectedTopic.resources[0].title}
                    </div>
                    <div style={{ fontSize: 14, lineHeight: 1.8, color: "var(--text-primary)", whiteSpace: "pre-wrap" }}>
                      {selectedTopic.resources[0].content_text}
                    </div>
                  </div>
                ) : (
                  <div style={{ color: "var(--text-muted)", padding: 20 }}>No uploaded notes for this topic yet.</div>
                )}
              </div>
            </div>
          ) : (
            <div style={{ textAlign: "center", padding: "60px 0" }}>Select a topic from the curriculum hierarchy.</div>
          )}
        </div>
      </div>
    </div>
  );
};

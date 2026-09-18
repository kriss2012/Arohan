import React, { useState, useEffect, useRef } from "react";
import { 
  Clock, ShieldAlert, CheckCircle, Flag, ChevronLeft, 
  ChevronRight, Send, AlertTriangle, Trophy, ArrowRight, RotateCcw
} from "lucide-react";
import { api } from "../services/api";
import { AttemptData, ScoreResult } from "../types";

interface ExamPlayerProps {
  examId: string;
  onExit: () => void;
  onFinished: () => void;
}

export const ExamPlayer: React.FC<ExamPlayerProps> = ({ examId, onExit, onFinished }) => {
  const [attempt, setAttempt] = useState<AttemptData | null>(null);
  const [currentIndex, setCurrentIndex] = useState<number>(0);
  const [responses, setResponses] = useState<Record<string, { optionId?: string; isMarked: boolean }>>({});
  const [remainingTime, setRemainingTime] = useState<number>(900); // 15 mins default
  const [scoreResult, setScoreResult] = useState<ScoreResult | null>(null);
  const [submitting, setSubmitting] = useState<boolean>(false);
  const [integrityCount, setIntegrityCount] = useState<number>(0);
  const [toastMessage, setToastMessage] = useState<string | null>(null);
  const startTimeRef = useRef<number>(Date.now());

  // Load Exam
  useEffect(() => {
    api.startAttempt(examId).then((att) => {
      setAttempt(att);
      setRemainingTime(att.remaining_seconds);
      // Populate saved responses
      const initialMap: Record<string, { optionId?: string; isMarked: boolean }> = {};
      att.saved_responses.forEach((r) => {
        initialMap[r.question_id] = { optionId: r.selected_option_id, isMarked: r.is_marked_for_review };
      });
      setResponses(initialMap);
    }).catch((err) => {
      alert(`Could not start exam: ${err.message}`);
      onExit();
    });
  }, [examId]);

  // Timer Countdown
  useEffect(() => {
    if (!attempt || scoreResult) return;
    const interval = setInterval(() => {
      setRemainingTime((prev) => {
        if (prev <= 1) {
          clearInterval(interval);
          handleSubmit();
          return 0;
        }
        return prev - 1;
      });
    }, 1000);
    return () => clearInterval(interval);
  }, [attempt, scoreResult]);

  // Environmental Integrity Monitoring (Window Focus & Keyboard Restrictions)
  useEffect(() => {
    if (!attempt || scoreResult) return;

    let blurStart = 0;
    const handleBlur = () => {
      blurStart = Date.now();
    };

    const handleFocus = () => {
      if (blurStart > 0) {
        const durationSec = ((Date.now() - blurStart) / 1000).toFixed(1);
        api.logIntegrityEvent(attempt.id, "FOCUS_LOST", "LOW", { duration_seconds: parseFloat(durationSec) });
        setIntegrityCount((c) => c + 1);
        showToast("Notice: Window focus lost briefly. Signal logged to exam audit.");
        blurStart = 0;
      }
    };

    const handleKeyDown = (e: KeyboardEvent) => {
      if ((e.ctrlKey && (e.key === "c" || e.key === "v" || e.key === "u")) || e.key === "F12") {
        e.preventDefault();
        api.logIntegrityEvent(attempt.id, "CLIPBOARD_COPY", "LOW", { key: e.key });
        setIntegrityCount((c) => c + 1);
        showToast("System notice: Clipboard & developer shortcuts are restricted.");
      }
    };

    window.addEventListener("blur", handleBlur);
    window.addEventListener("focus", handleFocus);
    window.addEventListener("keydown", handleKeyDown);

    return () => {
      window.removeEventListener("blur", handleBlur);
      window.removeEventListener("focus", handleFocus);
      window.removeEventListener("keydown", handleKeyDown);
    };
  }, [attempt, scoreResult]);

  const showToast = (msg: string) => {
    setToastMessage(msg);
    setTimeout(() => setToastMessage(null), 4000);
  };

  const handleSelectOption = (questionId: string, optionId: string) => {
    const elapsed = ((Date.now() - startTimeRef.current) / 1000);
    startTimeRef.current = Date.now();

    const currentMark = responses[questionId]?.isMarked || false;
    setResponses((prev) => ({
      ...prev,
      [questionId]: { optionId, isMarked: currentMark }
    }));

    if (attempt) {
      api.saveResponse(attempt.id, questionId, optionId, currentMark, elapsed);
    }
  };

  const toggleMarkForReview = (questionId: string) => {
    const currentOpt = responses[questionId]?.optionId;
    const newMark = !responses[questionId]?.isMarked;

    setResponses((prev) => ({
      ...prev,
      [questionId]: { optionId: currentOpt, isMarked: newMark }
    }));

    if (attempt) {
      api.saveResponse(attempt.id, questionId, currentOpt || null, newMark, 0);
    }
  };

  const handleSubmit = async () => {
    if (!attempt || submitting) return;
    setSubmitting(true);
    try {
      const res = await api.submitAttempt(attempt.id);
      setScoreResult(res);
    } catch (err: any) {
      alert(`Submission error: ${err.message}`);
    } finally {
      setSubmitting(false);
    }
  };

  const formatTimer = (seconds: number) => {
    const m = Math.floor(seconds / 60);
    const s = seconds % 60;
    return `${m.toString().padStart(2, "0")}:${s.toString().padStart(2, "0")}`;
  };

  if (!attempt) {
    return (
      <div style={{ display: "flex", alignItems: "center", justifyContent: "center", height: "100vh", background: "var(--imrd-navy)", color: "#ffffff" }}>
        Loading secure MCAT examination session...
      </div>
    );
  }

  // Final Results Screen
  if (scoreResult) {
    return (
      <div className="kiosk-fullscreen" style={{ alignItems: "center", justifyContent: "center", padding: 20 }}>
        <div className="card" style={{ maxWidth: 640, width: "100%", textAlign: "center", padding: 40, boxShadow: "var(--shadow-xl)" }}>
          <div style={{ display: "inline-flex", padding: 16, background: "var(--imrd-emerald-light)", borderRadius: "50%", marginBottom: 16 }}>
            <Trophy size={48} color="var(--imrd-emerald)" />
          </div>
          <h2 style={{ fontSize: 26, marginBottom: 8 }}>MCAT Diagnostic Completed</h2>
          <p style={{ color: "var(--text-secondary)", marginBottom: 24 }}>
            Your assessment results have been processed and fed directly into the <strong>AROHAN AI</strong> knowledge model.
          </p>

          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: 16, marginBottom: 24 }}>
            <div style={{ background: "var(--bg-slate)", padding: 16, borderRadius: "var(--radius-md)" }}>
              <div style={{ fontSize: 24, fontWeight: 800, color: "var(--imrd-blue)" }}>{scoreResult.score_percentage}%</div>
              <div style={{ fontSize: 12, color: "var(--text-muted)" }}>Overall Score</div>
            </div>
            <div style={{ background: "var(--imrd-emerald-light)", padding: 16, borderRadius: "var(--radius-md)" }}>
              <div style={{ fontSize: 24, fontWeight: 800, color: "var(--imrd-emerald)" }}>{scoreResult.total_correct}</div>
              <div style={{ fontSize: 12, color: "var(--text-secondary)" }}>Correct Answers</div>
            </div>
            <div style={{ background: "var(--bg-slate)", padding: 16, borderRadius: "var(--radius-md)" }}>
              <div style={{ fontSize: 24, fontWeight: 800, color: "var(--text-primary)" }}>{scoreResult.integrity_signal_count}</div>
              <div style={{ fontSize: 12, color: "var(--text-muted)" }}>Audit Signals</div>
            </div>
          </div>

          {/* Category Breakdown */}
          <div style={{ textAlign: "left", marginBottom: 24, background: "var(--surface-hover)", padding: 16, borderRadius: "var(--radius-md)" }}>
            <h4 style={{ fontSize: 14, marginBottom: 12 }}>Domain Performance Breakdown:</h4>
            {Object.entries(scoreResult.category_scores).map(([cat, score]) => (
              <div key={cat} style={{ display: "flex", justifyContent: "space-between", fontSize: 13, padding: "4px 0" }}>
                <span style={{ color: "var(--text-secondary)" }}>{cat}</span>
                <span style={{ fontWeight: 700, color: score < 50 ? "var(--imrd-ruby)" : "var(--imrd-emerald)" }}>{score}%</span>
              </div>
            ))}
          </div>

          <div style={{ display: "flex", gap: 12, justifyContent: "center" }}>
            <button className="btn btn-primary" onClick={() => { onFinished(); onExit(); }}>
              Return to Student Command Center <ArrowRight size={16} />
            </button>
          </div>
        </div>
      </div>
    );
  }

  const currentQ = attempt.questions[currentIndex];
  const currentResp = responses[currentQ.id];

  return (
    <div className="kiosk-fullscreen">
      {/* Toast alert */}
      {toastMessage && (
        <div style={{ position: "fixed", top: 80, right: 30, background: "var(--imrd-navy)", color: "#ffffff", padding: "12px 20px", borderRadius: "var(--radius-md)", boxShadow: "var(--shadow-lg)", display: "flex", alignItems: "center", gap: 10, zIndex: 1000, fontSize: 13 }}>
          <AlertTriangle color="var(--imrd-gold-accent)" size={18} /> {toastMessage}
        </div>
      )}

      {/* Kiosk Header */}
      <div className="kiosk-header">
        <div>
          <div style={{ fontSize: 11, color: "#93c5fd", textTransform: "uppercase", letterSpacing: "0.05em" }}>
            Modular Computerized Aptitude Test (MCAT)
          </div>
          <h3 style={{ color: "#ffffff", fontSize: 18 }}>{attempt.exam_title}</h3>
        </div>

        <div style={{ display: "flex", alignItems: "center", gap: "clamp(10px, 2vw, 24px)", flexWrap: "wrap" }}>
          <div style={{ display: "flex", alignItems: "center", gap: 8, background: "rgba(255, 255, 255, 0.1)", padding: "6px 14px", borderRadius: "var(--radius-sm)" }}>
            <Clock size={16} color="var(--imrd-gold-accent)" />
            <span style={{ fontFamily: "monospace", fontSize: 18, fontWeight: 700 }}>{formatTimer(remainingTime)}</span>
          </div>

          <div style={{ display: "flex", alignItems: "center", gap: 6, fontSize: 12, color: "#94a3b8" }}>
            <ShieldAlert size={14} color={integrityCount > 0 ? "var(--imrd-gold-accent)" : "#94a3b8"} />
            Audit Status: Active ({integrityCount} signals)
          </div>
        </div>
      </div>

      {/* Kiosk Body */}
      <div className="kiosk-body">
        {/* Left Navigator */}
        <div className="kiosk-nav">
          <h4 style={{ fontSize: 13, textTransform: "uppercase", letterSpacing: "0.05em", color: "var(--text-muted)" }}>
            Question Palette ({attempt.questions.length})
          </h4>
          <div className="question-grid">
            {attempt.questions.map((q, idx) => {
              const resp = responses[q.id];
              let statusClass = "";
              if (idx === currentIndex) statusClass = "current";
              else if (resp?.isMarked) statusClass = "marked";
              else if (resp?.optionId) statusClass = "answered";

              return (
                <button
                  key={q.id}
                  className={`q-btn ${statusClass}`}
                  onClick={() => setCurrentIndex(idx)}
                >
                  {idx + 1}
                </button>
              );
            })}
          </div>

          <div style={{ marginTop: "auto", fontSize: 11, color: "var(--text-muted)", display: "flex", flexDirection: "column", gap: 6 }}>
            <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
              <div style={{ width: 12, height: 12, borderRadius: 2, background: "var(--imrd-emerald)" }} /> Answered
            </div>
            <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
              <div style={{ width: 12, height: 12, borderRadius: 2, background: "var(--imrd-gold)" }} /> Marked for Review
            </div>
            <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
              <div style={{ width: 12, height: 12, borderRadius: 2, background: "var(--bg-slate)", border: "1px solid var(--border-subtle)" }} /> Not Attempted
            </div>
          </div>
        </div>

        {/* Central Question View */}
        <div className="kiosk-question-area">
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 20, flexWrap: "wrap", gap: 8 }}>
            <span className="badge badge-blue">{currentQ.category} • {currentQ.subcategory}</span>
            <span style={{ fontSize: 12, color: "var(--text-muted)" }}>Question {currentIndex + 1} of {attempt.questions.length}</span>
          </div>

          <h3 style={{ fontSize: "clamp(16px, 3vw, 18px)", lineHeight: 1.6, marginBottom: 24, fontWeight: 600 }}>
            {currentQ.question_text}
          </h3>

          {/* Options */}
          <div style={{ display: "flex", flexDirection: "column", gap: 12, maxWidth: 720 }}>
            {currentQ.options.map((opt) => {
              const isSelected = currentResp?.optionId === opt.id;
              return (
                <div
                  key={opt.id}
                  onClick={() => handleSelectOption(currentQ.id, opt.id)}
                  style={{
                    display: "flex",
                    alignItems: "center",
                    gap: "clamp(10px, 2vw, 16px)",
                    padding: "clamp(10px, 2vw, 14px) clamp(12px, 2.5vw, 20px)",
                    borderRadius: "var(--radius-md)",
                    border: isSelected ? "2px solid var(--imrd-blue)" : "1px solid var(--border-subtle)",
                    background: isSelected ? "var(--imrd-blue-subtle)" : "var(--surface-white)",
                    cursor: "pointer",
                    transition: "all 0.15s ease",
                    wordBreak: "break-word"
                  }}
                >
                  <div style={{
                    width: 28,
                    height: 28,
                    borderRadius: "50%",
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "center",
                    fontWeight: 700,
                    fontSize: 13,
                    background: isSelected ? "var(--imrd-blue)" : "var(--bg-slate)",
                    color: isSelected ? "#ffffff" : "var(--text-secondary)",
                    flexShrink: 0
                  }}>
                    {opt.option_key}
                  </div>
                  <div style={{ fontSize: 14, fontWeight: isSelected ? 600 : 400 }}>{opt.option_text}</div>
                </div>
              );
            })}
          </div>
        </div>
      </div>

      {/* Kiosk Footer */}
      <div className="kiosk-footer">
        <div style={{ display: "flex", gap: 10, flexWrap: "wrap" }}>
          <button
            className="btn btn-secondary"
            disabled={currentIndex === 0}
            onClick={() => setCurrentIndex((c) => c - 1)}
          >
            <ChevronLeft size={16} /> Previous
          </button>
          <button
            className="btn btn-secondary"
            style={{ color: currentResp?.isMarked ? "var(--imrd-gold)" : "var(--text-secondary)" }}
            onClick={() => toggleMarkForReview(currentQ.id)}
          >
            <Flag size={16} /> {currentResp?.isMarked ? "Unmark Review" : "Mark for Review"}
          </button>
        </div>

        <div style={{ display: "flex", gap: 10, flexWrap: "wrap" }}>
          {currentIndex < attempt.questions.length - 1 ? (
            <button
              className="btn btn-primary"
              onClick={() => setCurrentIndex((c) => c + 1)}
            >
              Next <ChevronRight size={16} />
            </button>
          ) : (
            <button
              className="btn btn-gold"
              onClick={handleSubmit}
              disabled={submitting}
            >
              <Send size={16} /> {submitting ? "Submitting..." : "Submit Examination"}
            </button>
          )}
        </div>
      </div>
    </div>
  );
};

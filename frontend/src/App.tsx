import React, { useState, useEffect } from "react";
import {
  GraduationCap, LayoutDashboard, BookOpen, Award, Users,
  ShieldCheck, Briefcase, LogOut, Clock, Brain, UserCheck,
  ShieldAlert, KeyRound, Shield, Settings, Menu, X
} from "lucide-react";
import { api } from "./services/api";
import { UserSummary } from "./types";
import { AuthScreen } from "./components/AuthScreen";
import { ChangePasswordModal } from "./components/ChangePasswordModal";
import { AdminUserManagement } from "./components/AdminUserManagement";
import { StudentDashboard } from "./components/StudentDashboard";
import { CurriculumView } from "./components/CurriculumView";
import { FacultyPortal } from "./components/FacultyPortal";
import { ExamControllerView } from "./components/ExamControllerView";
import { PlacementView } from "./components/PlacementView";
import { EvidenceDrawer } from "./components/EvidenceDrawer";
import { ExamPlayer } from "./components/ExamPlayer";

export const App: React.FC = () => {
  const [currentUser, setCurrentUser] = useState<UserSummary | null>(null);
  const [activeTab, setActiveTab] = useState<string>("dashboard");
  const [activeEvidenceSkillId, setActiveEvidenceSkillId] = useState<string | null>(null);
  const [activeExamId, setActiveExamId] = useState<string | null>(null);
  const [clockTime, setClockTime] = useState<string>("");
  const [loading, setLoading] = useState<boolean>(true);
  const [isChangePasswordOpen, setIsChangePasswordOpen] = useState<boolean>(false);
  const [isMobileNavOpen, setIsMobileNavOpen] = useState<boolean>(false);

  // Close mobile navigation drawer on Escape key
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape") {
        setIsMobileNavOpen(false);
      }
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, []);

  // Check existing session token on mount
  useEffect(() => {
    const restoreSession = async () => {
      const token = api.getToken();
      if (token) {
        try {
          const user = await api.getMe();
          setCurrentUser(user);
          routeInitialTab(user);
        } catch (err) {
          console.warn("Session expired or invalid token:", err);
          api.setToken(null);
          setCurrentUser(null);
        }
      }
      setLoading(false);
    };

    restoreSession();
  }, []);

  // Server clock ticker
  useEffect(() => {
    const timer = setInterval(() => {
      setClockTime(new Date().toLocaleTimeString());
    }, 1000);
    return () => clearInterval(timer);
  }, []);

  const routeInitialTab = (user: UserSummary) => {
    if (user.roles.includes("SUPER_ADMIN") || user.roles.includes("INSTITUTE_ADMIN")) {
      setActiveTab("admin");
    } else if (user.roles.includes("EXAM_CONTROLLER")) {
      setActiveTab("exam-controller");
    } else if (user.roles.includes("FACULTY")) {
      setActiveTab("faculty");
    } else {
      setActiveTab("dashboard");
    }
  };

  const handleLoginSuccess = (user: UserSummary) => {
    setCurrentUser(user);
    routeInitialTab(user);
  };

  const handleLogout = async () => {
    setLoading(true);
    try {
      await api.logout();
    } finally {
      setCurrentUser(null);
      setActiveTab("dashboard");
      setLoading(false);
    }
  };

  const loginAs = async (email: string, pw: string) => {
    setLoading(true);
    try {
      const res = await api.login(email, pw);
      setCurrentUser(res.user);
      routeInitialTab(res.user);
    } catch (err: any) {
      console.error("Quick login failure", err);
      alert(`Quick login failed: ${err.message}`);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div style={{ display: "flex", alignItems: "center", justifyContent: "center", height: "100vh", background: "var(--bg-slate)", color: "var(--imrd-navy)" }}>
        Loading Institute Student Development Platform...
      </div>
    );
  }

  // Not authenticated: render production-ready AuthScreen
  if (!currentUser) {
    return <AuthScreen onLoginSuccess={handleLoginSuccess} />;
  }

  // If inside an active high-stakes exam session
  if (activeExamId) {
    return (
      <ExamPlayer
        examId={activeExamId}
        onExit={() => setActiveExamId(null)}
        onFinished={() => setActiveTab("dashboard")}
      />
    );
  }

  const isAdmin = currentUser.roles.some((r) => ["SUPER_ADMIN", "INSTITUTE_ADMIN"].includes(r));
  const isFaculty = currentUser.roles.includes("FACULTY") || isAdmin;
  const isExamController = currentUser.roles.includes("EXAM_CONTROLLER") || isAdmin;

  const handleTabSelect = (tab: string) => {
    setActiveTab(tab);
    setIsMobileNavOpen(false);
  };

  return (
    <div className="app-container">
      {/* Mobile Drawer Backdrop */}
      <div
        className={`sidebar-backdrop ${isMobileNavOpen ? "active" : ""}`}
        onClick={() => setIsMobileNavOpen(false)}
        aria-hidden="true"
      />

      {/* Left Institutional Sidebar / Mobile Slide-Over Drawer */}
      <aside className={`sidebar ${isMobileNavOpen ? "mobile-open" : ""}`} aria-label="Main Navigation">
        <div className="sidebar-header" style={{ display: "flex", flexDirection: "column", alignItems: "center", textAlign: "center", padding: "20px 16px 16px", position: "relative" }}>
          {isMobileNavOpen && (
            <button
              onClick={() => setIsMobileNavOpen(false)}
              style={{
                position: "absolute", top: 12, right: 12,
                background: "rgba(255,255,255,0.1)", border: "none",
                borderRadius: "50%", color: "#ffffff", padding: 6,
                cursor: "pointer", display: "flex", alignItems: "center", justifyContent: "center"
              }}
              aria-label="Close navigation"
            >
              <X size={18} />
            </button>
          )}
          <img
            src="/logo.png"
            alt="AROHAN Logo"
            className="brand-logo-img"
            style={{ marginBottom: 12 }}
          />
          <div className="brand-badge" style={{ marginBottom: 4 }}>
            <GraduationCap size={14} /> IMRD SHIRPUR
          </div>
          <div className="brand-title">ISDP CAMPUS</div>
          <div className="brand-sub">AROHAN AI • MCAT LMS</div>
        </div>

        <nav className="nav-menu">
          <div className="nav-section-title">Student Corner</div>
          <button
            className={`nav-item ${activeTab === "dashboard" ? "active" : ""}`}
            onClick={() => handleTabSelect("dashboard")}
          >
            <LayoutDashboard size={18} /> Command Center
          </button>
          <button
            className={`nav-item ${activeTab === "curriculum" ? "active" : ""}`}
            onClick={() => handleTabSelect("curriculum")}
          >
            <BookOpen size={18} /> Curriculum Syllabus
          </button>
          <button
            className={`nav-item ${activeTab === "placement" ? "active" : ""}`}
            onClick={() => handleTabSelect("placement")}
          >
            <Briefcase size={18} /> Placement Readiness
          </button>

          <div className="nav-section-title">Faculty & Administration</div>
          {isFaculty && (
            <button
              className={`nav-item ${activeTab === "faculty" ? "active" : ""}`}
              onClick={() => handleTabSelect("faculty")}
            >
              <Users size={18} /> Faculty Remediation
            </button>
          )}

          {isExamController && (
            <button
              className={`nav-item ${activeTab === "exam-controller" ? "active" : ""}`}
              onClick={() => handleTabSelect("exam-controller")}
            >
              <ShieldCheck size={18} /> Exam Controller Live
            </button>
          )}

          {isAdmin && (
            <button
              className={`nav-item ${activeTab === "admin" ? "active" : ""}`}
              onClick={() => handleTabSelect("admin")}
            >
              <Shield size={18} /> Admin & Security
            </button>
          )}

          {/* Quick Account Controls for Mobile */}
          <div className="nav-section-title" style={{ marginTop: 12 }}>Account & Security</div>
          <button
            className="nav-item"
            onClick={() => { setIsMobileNavOpen(false); setIsChangePasswordOpen(true); }}
          >
            <KeyRound size={18} /> Change Password
          </button>
          <button
            className="nav-item"
            onClick={() => { setIsMobileNavOpen(false); handleLogout(); }}
            style={{ color: "var(--imrd-ruby-border)" }}
          >
            <LogOut size={18} /> Sign Out
          </button>
        </nav>

        {/* Persona Switcher for pair-programming, QA & verification */}
        <div className="sidebar-footer">
          <div style={{ fontSize: 11, color: "#94a3b8", marginBottom: 8, textTransform: "uppercase", letterSpacing: "0.05em" }}>
            Switch Role Persona:
          </div>
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 6 }}>
            <button
              onClick={() => { loginAs("student1@imrd.ac.in", "Student@123"); setIsMobileNavOpen(false); }}
              style={{
                fontSize: 11, padding: "6px 6px", borderRadius: 4, cursor: "pointer",
                background: currentUser.roles.includes("STUDENT") ? "var(--imrd-blue)" : "rgba(255,255,255,0.1)",
                color: "#ffffff", border: "none"
              }}
            >
              Student
            </button>
            <button
              onClick={() => { loginAs("faculty1@imrd.ac.in", "Faculty@123"); setIsMobileNavOpen(false); }}
              style={{
                fontSize: 11, padding: "6px 6px", borderRadius: 4, cursor: "pointer",
                background: currentUser.roles.includes("FACULTY") ? "var(--imrd-blue)" : "rgba(255,255,255,0.1)",
                color: "#ffffff", border: "none"
              }}
            >
              Faculty
            </button>
            <button
              onClick={() => { loginAs("controller@imrd.ac.in", "Exam@123"); setIsMobileNavOpen(false); }}
              style={{
                fontSize: 11, padding: "6px 6px", borderRadius: 4, cursor: "pointer",
                background: currentUser.roles.includes("EXAM_CONTROLLER") ? "var(--imrd-blue)" : "rgba(255,255,255,0.1)",
                color: "#ffffff", border: "none"
              }}
            >
              Controller
            </button>
            <button
              onClick={() => { loginAs("admin@imrd.ac.in", "Admin@123"); setIsMobileNavOpen(false); }}
              style={{
                fontSize: 11, padding: "6px 6px", borderRadius: 4, cursor: "pointer",
                background: currentUser.roles.includes("INSTITUTE_ADMIN") ? "var(--imrd-blue)" : "rgba(255,255,255,0.1)",
                color: "#ffffff", border: "none"
              }}
            >
              Admin
            </button>
          </div>
        </div>
      </aside>

      {/* Main Content Area */}
      <div className="main-wrapper">
        {/* Top Navbar */}
        <header className="top-navbar">
          <div className="top-navbar-left">
            <button
              className="mobile-nav-toggle"
              onClick={() => setIsMobileNavOpen(!isMobileNavOpen)}
              aria-label={isMobileNavOpen ? "Close navigation drawer" : "Open navigation drawer"}
              title="Toggle Menu"
            >
              {isMobileNavOpen ? <X size={20} /> : <Menu size={20} />}
            </button>
            <img
              src="/logo.png"
              alt="AROHAN Logo"
              style={{ width: 34, height: 34, borderRadius: 8, objectFit: "contain", background: "#ffffff", padding: 2, boxShadow: "0 2px 6px rgba(0,0,0,0.15)" }}
            />
            <div className="academic-badge">
              <ShieldCheck size={14} /> <span><span className="hide-on-mobile">RC Patel Educational Trust's </span>IMRD</span>
            </div>
            <div className="hide-on-mobile" style={{ fontSize: 13, color: "var(--text-muted)", display: "flex", alignItems: "center", gap: 6 }}>
              <Brain size={14} color="var(--imrd-blue)" /> <span className="hide-on-tablet">AROHAN Bayesian Engine Active</span>
            </div>
          </div>

          <div className="top-navbar-right">
            <div className="server-clock hide-on-mobile">
              <Clock size={14} /> {clockTime}
            </div>

            <div className="user-pill" title={`${currentUser.first_name} ${currentUser.last_name} (${currentUser.roles.join(", ")})`}>
              <div className="user-avatar">
                {currentUser.first_name[0]}{currentUser.last_name[0]}
              </div>
              <div className="hide-on-mobile" style={{ lineHeight: 1.2, minWidth: 0, overflow: "hidden" }}>
                <div style={{ fontSize: 13, fontWeight: 700, textOverflow: "ellipsis", overflow: "hidden", whiteSpace: "nowrap" }}>
                  {currentUser.first_name} {currentUser.last_name}
                </div>
                <div style={{ fontSize: 11, color: "var(--text-muted)", textOverflow: "ellipsis", overflow: "hidden", whiteSpace: "nowrap" }}>
                  {currentUser.roles[0]}
                </div>
              </div>
            </div>

            {/* Change Password & Logout Buttons */}
            <button
              className="btn btn-secondary hide-on-mobile"
              onClick={() => setIsChangePasswordOpen(true)}
              style={{ fontSize: 12, padding: "6px 10px", display: "flex", alignItems: "center", gap: 6 }}
              title="Security: Change Password"
            >
              <KeyRound size={14} /> Password
            </button>

            <button
              className="btn btn-secondary"
              onClick={handleLogout}
              style={{
                fontSize: 12, padding: "6px 10px", display: "flex", alignItems: "center", gap: 6,
                color: "var(--imrd-ruby)", borderColor: "var(--imrd-ruby-border)"
              }}
              title="Secure Logout"
            >
              <LogOut size={14} /> <span className="hide-on-mobile">Sign Out</span>
            </button>
          </div>
        </header>

        {/* Dynamic Content Body */}
        <main className="content-body">
          {activeTab === "dashboard" && (
            <StudentDashboard
              user={currentUser}
              onOpenEvidence={(skillId) => setActiveEvidenceSkillId(skillId)}
              onStartExam={(examId) => setActiveExamId(examId)}
              onNavigateTab={(tab) => setActiveTab(tab)}
            />
          )}

          {activeTab === "curriculum" && <CurriculumView />}

          {activeTab === "faculty" && <FacultyPortal />}

          {activeTab === "exam-controller" && <ExamControllerView />}

          {activeTab === "placement" && <PlacementView studentId={currentUser.id} />}

          {activeTab === "admin" && <AdminUserManagement />}
        </main>
      </div>

      {/* "Why am I seeing this?" Evidence Drawer */}
      <EvidenceDrawer
        skillId={activeEvidenceSkillId}
        onClose={() => setActiveEvidenceSkillId(null)}
      />

      {/* Change Password Modal */}
      <ChangePasswordModal
        isOpen={isChangePasswordOpen}
        onClose={() => setIsChangePasswordOpen(false)}
      />

      {/* Institutional Watermark - LOGIC LEGEND */}
      <div className="app-watermark-fixed" title="LOGIC LEGEND • Ideas Today • Impact Tomorrow" />
    </div>
  );
};
export default App;

import React, { useState, useEffect } from "react";
import { 
  Users, UserPlus, Shield, ShieldAlert, ShieldCheck, Mail, 
  Lock, RefreshCw, KeyRound, AlertTriangle, CheckCircle2, 
  Search, X, UserX, Clock
} from "lucide-react";
import { api } from "../services/api";

interface AdminUserManagementProps {
  onRefreshStats?: () => void;
}

export const AdminUserManagement: React.FC<AdminUserManagementProps> = ({ onRefreshStats }) => {
  const [users, setUsers] = useState<any[]>([]);
  const [authorizedUsers, setAuthorizedUsers] = useState<any[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [activeSubTab, setActiveSubTab] = useState<"users" | "allowlist">("users");
  const [searchTerm, setSearchTerm] = useState<string>("");
  const [notification, setNotification] = useState<{ type: "success" | "error"; message: string } | null>(null);

  // New user modal
  const [showAddModal, setShowAddModal] = useState<boolean>(false);
  const [fullName, setFullName] = useState<string>("");
  const [email, setEmail] = useState<string>("");
  const [intendedRole, setIntendedRole] = useState<string>("STUDENT");
  const [studentOrEmpId, setStudentOrEmpId] = useState<string>("");
  const [submitting, setSubmitting] = useState<boolean>(false);

  const fetchData = async () => {
    setLoading(true);
    try {
      const [uRes, aRes] = await Promise.all([
        api.getAdminUsers(),
        api.getAuthorizedUsers()
      ]);
      setUsers(uRes);
      setAuthorizedUsers(aRes);
    } catch (err: any) {
      setNotification({ type: "error", message: err.message || "Failed to load user administration data." });
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  const showFeedback = (type: "success" | "error", message: string) => {
    setNotification({ type, message });
    setTimeout(() => setNotification(null), 5000);
  };

  const handleAddUser = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!email.trim() || !fullName.trim()) {
      showFeedback("error", "Full name and email are required.");
      return;
    }

    setSubmitting(true);
    try {
      await api.addAuthorizedUser({
        email: email.trim().toLowerCase(),
        full_name: fullName.trim(),
        intended_role: intendedRole,
        student_or_emp_id: studentOrEmpId.trim() || undefined
      });
      showFeedback("success", `Authorized ${email} successfully! Invitation email generated in local archive.`);
      setShowAddModal(false);
      setFullName("");
      setEmail("");
      setStudentOrEmpId("");
      fetchData();
      if (onRefreshStats) onRefreshStats();
    } catch (err: any) {
      showFeedback("error", err.message || "Failed to authorize user.");
    } finally {
      setSubmitting(false);
    }
  };

  const handleDeactivate = async (userId: string, userEmail: string) => {
    if (!confirm(`Are you sure you want to deactivate ${userEmail}? Their active sessions will be immediately terminated.`)) return;
    try {
      await api.deactivateUser(userId);
      showFeedback("success", `Account ${userEmail} deactivated and sessions revoked.`);
      fetchData();
    } catch (err: any) {
      showFeedback("error", err.message || "Failed to deactivate user.");
    }
  };

  const handleReactivate = async (userId: string, userEmail: string) => {
    try {
      await api.reactivateUser(userId);
      showFeedback("success", `Account ${userEmail} successfully reactivated.`);
      fetchData();
    } catch (err: any) {
      showFeedback("error", err.message || "Failed to reactivate user.");
    }
  };

  const handleUnlock = async (userId: string, userEmail: string) => {
    try {
      await api.unlockUser(userId);
      showFeedback("success", `Lockout reset for ${userEmail}.`);
      fetchData();
    } catch (err: any) {
      showFeedback("error", err.message || "Failed to unlock user.");
    }
  };

  const handleResend = async (userId: string, userEmail: string) => {
    try {
      await api.resendInvitation(userId);
      showFeedback("success", `Account invitation resent to ${userEmail}. Check local email archive.`);
    } catch (err: any) {
      showFeedback("error", err.message || "Failed to resend invitation.");
    }
  };

  // Filtered lists
  const filteredUsers = users.filter(u => 
    u.email.toLowerCase().includes(searchTerm.toLowerCase()) ||
    `${u.first_name} ${u.last_name}`.toLowerCase().includes(searchTerm.toLowerCase()) ||
    (u.roles && u.roles.some((r: string) => r.toLowerCase().includes(searchTerm.toLowerCase())))
  );

  const filteredAllowlist = authorizedUsers.filter(a =>
    a.email.toLowerCase().includes(searchTerm.toLowerCase()) ||
    (a.full_name && a.full_name.toLowerCase().includes(searchTerm.toLowerCase())) ||
    (a.student_or_emp_id && a.student_or_emp_id.toLowerCase().includes(searchTerm.toLowerCase()))
  );

  const stats = {
    totalAccounts: users.length,
    activeAccounts: users.filter(u => u.is_active && u.status === "ACTIVE").length,
    setupPending: users.filter(u => !u.has_password || !u.is_email_verified).length,
    allowlistTotal: authorizedUsers.length,
    lockedOrInactive: users.filter(u => !u.is_active || u.status === "LOCKED" || u.status === "INACTIVE").length
  };

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 24 }}>
      {/* Header */}
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", flexWrap: "wrap", gap: 16 }}>
        <div>
          <div style={{ display: "inline-flex", alignItems: "center", gap: 6, padding: "4px 10px", borderRadius: "var(--radius-full)", background: "var(--imrd-navy-light)", color: "var(--imrd-navy)", fontSize: 12, fontWeight: 700, marginBottom: 8 }}>
            <ShieldCheck size={14} /> Institutional Security Console
          </div>
          <h1 style={{ fontSize: "clamp(20px, 4vw, 26px)", fontWeight: 800, color: "var(--imrd-navy)", letterSpacing: "-0.02em" }}>
            Admin User Authorization & Account Control
          </h1>
          <p style={{ fontSize: 14, color: "var(--text-muted)", marginTop: 4 }}>
            Enforce authorized-only onboarding: First-time OTP verification &rarr; Mandatory password creation &rarr; Session security.
          </p>
        </div>

        <div style={{ display: "flex", gap: 12, flexWrap: "wrap" }}>
          <button 
            className="btn btn-secondary" 
            onClick={fetchData}
            style={{ display: "flex", alignItems: "center", gap: 6 }}
          >
            <RefreshCw size={15} /> Refresh
          </button>
          <button 
            className="btn btn-navy" 
            onClick={() => setShowAddModal(true)}
            style={{ display: "flex", alignItems: "center", gap: 6 }}
          >
            <UserPlus size={16} /> Authorize New User
          </button>
        </div>
      </div>

      {/* Alerts */}
      {notification && (
        <div style={{
          display: "flex",
          alignItems: "center",
          gap: 10,
          padding: "12px 16px",
          borderRadius: "var(--radius-md)",
          fontSize: 14,
          fontWeight: 600,
          background: notification.type === "success" ? "var(--imrd-emerald-light)" : "var(--imrd-ruby-light)",
          color: notification.type === "success" ? "var(--imrd-emerald)" : "var(--imrd-ruby)",
          border: `1px solid ${notification.type === "success" ? "var(--imrd-emerald-border)" : "var(--imrd-ruby-border)"}`
        }}>
          {notification.type === "success" ? <CheckCircle2 size={18} /> : <AlertTriangle size={18} />}
          <span>{notification.message}</span>
        </div>
      )}

      {/* Metrics Cards */}
      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(200px, 1fr))", gap: 16 }}>
        <div className="card" style={{ padding: 16 }}>
          <div style={{ fontSize: 12, color: "var(--text-muted)", fontWeight: 600 }}>Total Authorized Allowlist</div>
          <div style={{ fontSize: 28, fontWeight: 800, color: "var(--imrd-navy)", marginTop: 4 }}>
            {stats.allowlistTotal}
          </div>
          <div style={{ fontSize: 11, color: "var(--text-muted)", marginTop: 2 }}>Institutional candidates authorized</div>
        </div>

        <div className="card" style={{ padding: 16 }}>
          <div style={{ fontSize: 12, color: "var(--text-muted)", fontWeight: 600 }}>Active Logged-In Users</div>
          <div style={{ fontSize: 28, fontWeight: 800, color: "var(--imrd-emerald)", marginTop: 4 }}>
            {stats.activeAccounts}
          </div>
          <div style={{ fontSize: 11, color: "var(--text-muted)", marginTop: 2 }}>Password setup & email verified</div>
        </div>

        <div className="card" style={{ padding: 16 }}>
          <div style={{ fontSize: 12, color: "var(--text-muted)", fontWeight: 600 }}>First-Time Setup Pending</div>
          <div style={{ fontSize: 28, fontWeight: 800, color: "var(--imrd-amber)", marginTop: 4 }}>
            {stats.setupPending}
          </div>
          <div style={{ fontSize: 11, color: "var(--text-muted)", marginTop: 2 }}>Awaiting OTP / password setup</div>
        </div>

        <div className="card" style={{ padding: 16 }}>
          <div style={{ fontSize: 12, color: "var(--text-muted)", fontWeight: 600 }}>Deactivated / Locked</div>
          <div style={{ fontSize: 28, fontWeight: 800, color: stats.lockedOrInactive > 0 ? "var(--imrd-ruby)" : "var(--text-muted)", marginTop: 4 }}>
            {stats.lockedOrInactive}
          </div>
          <div style={{ fontSize: 11, color: "var(--text-muted)", marginTop: 2 }}>Sessions blocked / access halted</div>
        </div>
      </div>

      {/* Search and Sub-tabs */}
      <div className="card" style={{ padding: 0, overflow: "hidden" }}>
        <div style={{ 
          display: "flex", 
          justifyContent: "space-between", 
          alignItems: "center", 
          padding: "16px clamp(12px, 2.5vw, 20px)", 
          borderBottom: "1px solid var(--border-subtle)",
          background: "var(--surface-light)",
          flexWrap: "wrap",
          gap: 12
        }}>
          <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
            <button
              onClick={() => setActiveSubTab("users")}
              style={{
                padding: "8px 16px",
                borderRadius: "var(--radius-sm)",
                border: "none",
                fontWeight: 700,
                fontSize: 13,
                cursor: "pointer",
                background: activeSubTab === "users" ? "var(--imrd-navy)" : "transparent",
                color: activeSubTab === "users" ? "#ffffff" : "var(--text-muted)"
              }}
            >
              System Accounts ({users.length})
            </button>
            <button
              onClick={() => setActiveSubTab("allowlist")}
              style={{
                padding: "8px 16px",
                borderRadius: "var(--radius-sm)",
                border: "none",
                fontWeight: 700,
                fontSize: 13,
                cursor: "pointer",
                background: activeSubTab === "allowlist" ? "var(--imrd-navy)" : "transparent",
                color: activeSubTab === "allowlist" ? "#ffffff" : "var(--text-muted)"
              }}
            >
              Authorized Allowlist ({authorizedUsers.length})
            </button>
          </div>

          <div style={{ position: "relative", minWidth: 200, flex: "1 1 240px", maxWidth: 400 }}>
            <Search size={15} style={{ position: "absolute", left: 10, top: "50%", transform: "translateY(-50%)", color: "var(--text-muted)" }} />
            <input
              type="text"
              placeholder="Search by name, email, role..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              style={{
                width: "100%",
                padding: "8px 12px 8px 32px",
                fontSize: 13,
                borderRadius: "var(--radius-sm)",
                border: "1px solid var(--border-subtle)",
                outline: "none"
              }}
            />
          </div>
        </div>

        {/* Tab 1: System Accounts */}
        {activeSubTab === "users" && (
          <div className="responsive-table-container">
            <table style={{ width: "100%", minWidth: "640px", borderCollapse: "collapse", fontSize: 13 }}>
              <thead>
                <tr style={{ background: "var(--surface-hover)", textAlign: "left", color: "var(--text-muted)", fontSize: 12 }}>
                  <th style={{ padding: "12px 16px" }}>User</th>
                  <th style={{ padding: "12px 16px" }}>Roles</th>
                  <th style={{ padding: "12px 16px" }}>Auth Lifecycle State</th>
                  <th style={{ padding: "12px 16px" }}>Last Login</th>
                  <th style={{ padding: "12px 16px", textAlign: "right" }}>Security Actions</th>
                </tr>
              </thead>
              <tbody>
                {filteredUsers.length === 0 ? (
                  <tr>
                    <td colSpan={5} style={{ padding: 32, textAlign: "center", color: "var(--text-muted)" }}>
                      {loading ? "Loading accounts..." : "No user accounts match the search criteria."}
                    </td>
                  </tr>
                ) : (
                  filteredUsers.map((u) => {
                    const isSetupPending = !u.has_password || !u.is_email_verified;
                    const isLocked = u.locked_until && new Date(u.locked_until) > new Date();

                    return (
                      <tr key={u.id} style={{ borderBottom: "1px solid var(--border-subtle)" }}>
                        <td style={{ padding: "14px 16px" }}>
                          <div style={{ fontWeight: 700, color: "var(--text-main)" }}>
                            {u.first_name} {u.last_name}
                          </div>
                          <div style={{ fontSize: 12, color: "var(--text-muted)", fontFamily: "monospace" }}>
                            {u.email}
                          </div>
                        </td>

                        <td style={{ padding: "14px 16px" }}>
                          <div style={{ display: "flex", flexWrap: "wrap", gap: 4 }}>
                            {u.roles?.map((r: string) => (
                              <span key={r} className="badge badge-blue" style={{ fontSize: 10 }}>
                                {r}
                              </span>
                            ))}
                          </div>
                        </td>

                        <td style={{ padding: "14px 16px" }}>
                          <div style={{ display: "flex", flexDirection: "column", gap: 4, alignItems: "flex-start" }}>
                            {!u.is_active || u.status === "INACTIVE" ? (
                              <span className="badge badge-ruby" style={{ display: "inline-flex", alignItems: "center", gap: 4 }}>
                                <UserX size={11} /> Deactivated
                              </span>
                            ) : isLocked ? (
                              <span className="badge badge-ruby" style={{ display: "inline-flex", alignItems: "center", gap: 4 }}>
                                <Lock size={11} /> Locked ({u.failed_login_attempts} fails)
                              </span>
                            ) : isSetupPending ? (
                              <span className="badge badge-amber" style={{ display: "inline-flex", alignItems: "center", gap: 4 }}>
                                <Clock size={11} /> Setup Pending (No Password)
                              </span>
                            ) : (
                              <span className="badge badge-emerald" style={{ display: "inline-flex", alignItems: "center", gap: 4 }}>
                                <ShieldCheck size={11} /> Fully Activated
                              </span>
                            )}

                            <div style={{ fontSize: 10, color: "var(--text-muted)" }}>
                              Auth: {u.is_authorized ? "Yes" : "No"} • Email Verified: {u.is_email_verified ? "Yes" : "No"}
                            </div>
                          </div>
                        </td>

                        <td style={{ padding: "14px 16px", color: "var(--text-muted)", fontSize: 12 }}>
                          {u.last_login_at ? new Date(u.last_login_at).toLocaleString() : "Never"}
                        </td>

                        <td style={{ padding: "14px 16px", textAlign: "right" }}>
                          <div style={{ display: "inline-flex", gap: 6 }}>
                            {isLocked && (
                              <button
                                className="btn btn-secondary"
                                style={{ fontSize: 11, padding: "4px 8px" }}
                                onClick={() => handleUnlock(u.id, u.email)}
                                title="Reset failed login counter and unlock"
                              >
                                Unlock
                              </button>
                            )}

                            <button
                              className="btn btn-secondary"
                              style={{ fontSize: 11, padding: "4px 8px" }}
                              onClick={() => handleResend(u.id, u.email)}
                              title="Resend invitation and activation instructions"
                            >
                              <Mail size={12} /> Invite
                            </button>

                            {u.is_active && u.status !== "INACTIVE" ? (
                              <button
                                style={{
                                  fontSize: 11, padding: "4px 8px", borderRadius: "var(--radius-sm)",
                                  background: "var(--imrd-ruby-light)", color: "var(--imrd-ruby)",
                                  border: "1px solid var(--imrd-ruby-border)", cursor: "pointer", fontWeight: 600
                                }}
                                onClick={() => handleDeactivate(u.id, u.email)}
                                title="Terminate active sessions and block login"
                              >
                                Deactivate
                              </button>
                            ) : (
                              <button
                                style={{
                                  fontSize: 11, padding: "4px 8px", borderRadius: "var(--radius-sm)",
                                  background: "var(--imrd-emerald-light)", color: "var(--imrd-emerald)",
                                  border: "1px solid var(--imrd-emerald-border)", cursor: "pointer", fontWeight: 600
                                }}
                                onClick={() => handleReactivate(u.id, u.email)}
                                title="Restore account login access"
                              >
                                Reactivate
                              </button>
                            )}
                          </div>
                        </td>
                      </tr>
                    );
                  })
                )}
              </tbody>
            </table>
          </div>
        )}

        {/* Tab 2: Authorized Allowlist */}
        {activeSubTab === "allowlist" && (
          <div className="responsive-table-container">
            <table style={{ width: "100%", minWidth: "640px", borderCollapse: "collapse", fontSize: 13 }}>
              <thead>
                <tr style={{ background: "var(--surface-hover)", textAlign: "left", color: "var(--text-muted)", fontSize: 12 }}>
                  <th style={{ padding: "12px 16px" }}>Authorized Individual</th>
                  <th style={{ padding: "12px 16px" }}>Intended Role</th>
                  <th style={{ padding: "12px 16px" }}>ID / Reg Number</th>
                  <th style={{ padding: "12px 16px" }}>Allowlist Status</th>
                  <th style={{ padding: "12px 16px" }}>Authorized Date</th>
                </tr>
              </thead>
              <tbody>
                {filteredAllowlist.length === 0 ? (
                  <tr>
                    <td colSpan={5} style={{ padding: 32, textAlign: "center", color: "var(--text-muted)" }}>
                      {loading ? "Loading allowlist..." : "No allowlist entries found."}
                    </td>
                  </tr>
                ) : (
                  filteredAllowlist.map((a) => (
                    <tr key={a.id} style={{ borderBottom: "1px solid var(--border-subtle)" }}>
                      <td style={{ padding: "14px 16px" }}>
                        <div style={{ fontWeight: 700, color: "var(--text-main)" }}>
                          {a.full_name}
                        </div>
                        <div style={{ fontSize: 12, color: "var(--text-muted)", fontFamily: "monospace" }}>
                          {a.email}
                        </div>
                      </td>

                      <td style={{ padding: "14px 16px" }}>
                        <span className="badge badge-blue">{a.intended_role}</span>
                      </td>

                      <td style={{ padding: "14px 16px", color: "var(--text-muted)" }}>
                        {a.student_or_emp_id || "—"}
                      </td>

                      <td style={{ padding: "14px 16px" }}>
                        {a.status === "ACTIVE" || a.status === "USED" ? (
                          <span className="badge badge-emerald" style={{ display: "inline-flex", alignItems: "center", gap: 4 }}>
                            <CheckCircle2 size={11} /> Activated
                          </span>
                        ) : (
                          <span className="badge badge-amber" style={{ display: "inline-flex", alignItems: "center", gap: 4 }}>
                            <Clock size={11} /> Invited (Pending First Login)
                          </span>
                        )}
                      </td>

                      <td style={{ padding: "14px 16px", color: "var(--text-muted)", fontSize: 12 }}>
                        {a.created_at ? new Date(a.created_at).toLocaleDateString() : "—"}
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Add Authorized User Modal */}
      {showAddModal && (
        <div style={{
          position: "fixed",
          top: 0,
          left: 0,
          right: 0,
          bottom: 0,
          background: "rgba(15, 23, 42, 0.65)",
          backdropFilter: "blur(4px)",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          zIndex: 1000,
          padding: 20
        }}>
          <div className="card" style={{ width: "100%", maxWidth: 500, padding: "clamp(18px, 4vw, 28px)", maxHeight: "90vh", overflowY: "auto", boxShadow: "var(--shadow-xl)" }}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 20 }}>
              <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
                <div style={{
                  width: 36, height: 36, borderRadius: "var(--radius-md)",
                  background: "var(--imrd-navy-light)", color: "var(--imrd-navy)",
                  display: "flex", alignItems: "center", justifyContent: "center"
                }}>
                  <UserPlus size={20} />
                </div>
                <div>
                  <h3 style={{ fontSize: 18, fontWeight: 700, color: "var(--imrd-navy)" }}>Authorize New User</h3>
                  <div style={{ fontSize: 12, color: "var(--text-muted)" }}>Grants first-time login authorization</div>
                </div>
              </div>
              <button 
                onClick={() => setShowAddModal(false)}
                style={{ background: "none", border: "none", cursor: "pointer", color: "var(--text-muted)" }}
              >
                <X size={20} />
              </button>
            </div>

            <form onSubmit={handleAddUser} style={{ display: "flex", flexDirection: "column", gap: 16 }}>
              <div>
                <label style={{ display: "block", fontSize: 13, fontWeight: 600, marginBottom: 6, color: "var(--text-main)" }}>
                  Full Name *
                </label>
                <input
                  type="text"
                  required
                  placeholder="e.g. Rahul Patil"
                  value={fullName}
                  onChange={(e) => setFullName(e.target.value)}
                  style={{
                    width: "100%",
                    padding: "10px 14px",
                    borderRadius: "var(--radius-sm)",
                    border: "1px solid var(--border-strong)",
                    fontSize: 14
                  }}
                />
              </div>

              <div>
                <label style={{ display: "block", fontSize: 13, fontWeight: 600, marginBottom: 6, color: "var(--text-main)" }}>
                  Authorized Institutional Email *
                </label>
                <input
                  type="email"
                  required
                  placeholder="e.g. rahul@imrd.ac.in"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  style={{
                    width: "100%",
                    padding: "10px 14px",
                    borderRadius: "var(--radius-sm)",
                    border: "1px solid var(--border-strong)",
                    fontSize: 14
                  }}
                />
                <div style={{ fontSize: 11, color: "var(--text-muted)", marginTop: 4 }}>
                  Only authorized emails can begin first-time account activation.
                </div>
              </div>

              <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(180px, 1fr))", gap: 12 }}>
                <div>
                  <label style={{ display: "block", fontSize: 13, fontWeight: 600, marginBottom: 6, color: "var(--text-main)" }}>
                    System Role *
                  </label>
                  <select
                    value={intendedRole}
                    onChange={(e) => setIntendedRole(e.target.value)}
                    style={{
                      width: "100%",
                      padding: "10px 14px",
                      borderRadius: "var(--radius-sm)",
                      border: "1px solid var(--border-strong)",
                      fontSize: 14,
                      background: "#ffffff"
                    }}
                  >
                    <option value="STUDENT">Student</option>
                    <option value="FACULTY">Faculty</option>
                    <option value="EXAM_CONTROLLER">Exam Controller</option>
                    <option value="INSTITUTE_ADMIN">Institute Admin</option>
                  </select>
                </div>

                <div>
                  <label style={{ display: "block", fontSize: 13, fontWeight: 600, marginBottom: 6, color: "var(--text-main)" }}>
                    Student / Employee ID
                  </label>
                  <input
                    type="text"
                    placeholder="e.g. MCA-2026-088"
                    value={studentOrEmpId}
                    onChange={(e) => setStudentOrEmpId(e.target.value)}
                    style={{
                      width: "100%",
                      padding: "10px 14px",
                      borderRadius: "var(--radius-sm)",
                      border: "1px solid var(--border-strong)",
                      fontSize: 14
                    }}
                  />
                </div>
              </div>

              <div style={{
                background: "var(--surface-hover)",
                padding: 12,
                borderRadius: "var(--radius-sm)",
                fontSize: 12,
                color: "var(--text-muted)",
                display: "flex",
                alignItems: "flex-start",
                gap: 8
              }}>
                <Mail size={16} color="var(--imrd-blue)" style={{ flexShrink: 0, marginTop: 2 }} />
                <div>
                  An official institutional invitation email with activation instructions will be automatically dispatched and archived locally in <code style={{ background: "rgba(0,0,0,0.06)", padding: "1px 4px", borderRadius: 3 }}>./local_storage/emails/</code>.
                </div>
              </div>

              <div style={{ display: "flex", justifyContent: "flex-end", gap: 12, marginTop: 8 }}>
                <button
                  type="button"
                  className="btn btn-secondary"
                  onClick={() => setShowAddModal(false)}
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="btn btn-navy"
                  disabled={submitting}
                  style={{ display: "flex", alignItems: "center", gap: 6 }}
                >
                  {submitting ? "Authorizing..." : "Authorize & Send Invitation"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
export default AdminUserManagement;

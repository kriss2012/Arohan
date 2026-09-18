import React, { useState } from "react";
import { Lock, Eye, EyeOff, CheckCircle2, AlertCircle, X, Shield } from "lucide-react";
import { api } from "../services/api";

interface ChangePasswordModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export const ChangePasswordModal: React.FC<ChangePasswordModalProps> = ({ isOpen, onClose }) => {
  const [currentPassword, setCurrentPassword] = useState<string>("");
  const [newPassword, setNewPassword] = useState<string>("");
  const [confirmPassword, setConfirmPassword] = useState<string>("");
  const [showCurrent, setShowCurrent] = useState<boolean>(false);
  const [showNew, setShowNew] = useState<boolean>(false);
  const [loading, setLoading] = useState<boolean>(false);
  const [errorMsg, setErrorMsg] = useState<string>("");
  const [successMsg, setSuccessMsg] = useState<string>("");

  if (!isOpen) return null;

  // Password Policy Checks
  const checks = {
    length: newPassword.length >= 12,
    upper: /[A-Z]/.test(newPassword),
    lower: /[a-z]/.test(newPassword),
    number: /[0-9]/.test(newPassword),
    special: /[!@#$%^&*()_+\-=\[\]{}|;:,.<>?]/.test(newPassword),
    matches: newPassword.length > 0 && newPassword === confirmPassword
  };

  const validCount = [checks.length, checks.upper, checks.lower, checks.number, checks.special].filter(Boolean).length;
  const strengthLevel = 
    validCount <= 2 ? "Weak" :
    validCount === 3 ? "Fair" :
    validCount === 4 ? "Good" : "Strong";

  const strengthColor =
    strengthLevel === "Weak" ? "var(--imrd-ruby)" :
    strengthLevel === "Fair" ? "var(--imrd-amber)" :
    strengthLevel === "Good" ? "var(--imrd-blue)" : "var(--imrd-emerald)";

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrorMsg("");
    setSuccessMsg("");

    if (!checks.length || !checks.upper || !checks.lower || !checks.number || !checks.special) {
      setErrorMsg("New password does not satisfy institutional security requirements.");
      return;
    }

    if (newPassword !== confirmPassword) {
      setErrorMsg("New passwords do not match.");
      return;
    }

    setLoading(true);
    try {
      await api.changePassword(currentPassword, newPassword, confirmPassword);
      setSuccessMsg("Password changed successfully! Other active sessions have been revoked.");
      setTimeout(() => {
        onClose();
        setCurrentPassword("");
        setNewPassword("");
        setConfirmPassword("");
        setSuccessMsg("");
      }, 2500);
    } catch (err: any) {
      setErrorMsg(err.message || "Failed to update password. Please check your current password.");
    } finally {
      setLoading(false);
    }
  };

  return (
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
      zIndex: 1100,
      padding: "clamp(12px, 3vw, 20px)"
    }}>
      <div className="card" style={{ width: "100%", maxWidth: 480, padding: "clamp(18px, 4vw, 28px)", maxHeight: "90vh", overflowY: "auto", boxShadow: "var(--shadow-xl)" }}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 20 }}>
          <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
            <div style={{
              width: 38, height: 38, borderRadius: "var(--radius-md)",
              background: "var(--imrd-navy-light)", color: "var(--imrd-navy)",
              display: "flex", alignItems: "center", justifyContent: "center"
            }}>
              <Lock size={20} />
            </div>
            <div>
              <h3 style={{ fontSize: 18, fontWeight: 700, color: "var(--imrd-navy)" }}>Change Account Password</h3>
              <div style={{ fontSize: 12, color: "var(--text-muted)" }}>Settings &rarr; Security Controls</div>
            </div>
          </div>
          <button 
            onClick={onClose}
            style={{ background: "none", border: "none", cursor: "pointer", color: "var(--text-muted)" }}
          >
            <X size={20} />
          </button>
        </div>

        {errorMsg && (
          <div style={{
            display: "flex", alignItems: "center", gap: 8, padding: "10px 14px",
            borderRadius: "var(--radius-sm)", background: "var(--imrd-ruby-light)",
            color: "var(--imrd-ruby)", fontSize: 13, fontWeight: 600, marginBottom: 16,
            border: "1px solid var(--imrd-ruby-border)"
          }}>
            <AlertCircle size={16} />
            <span>{errorMsg}</span>
          </div>
        )}

        {successMsg && (
          <div style={{
            display: "flex", alignItems: "center", gap: 8, padding: "10px 14px",
            borderRadius: "var(--radius-sm)", background: "var(--imrd-emerald-light)",
            color: "var(--imrd-emerald)", fontSize: 13, fontWeight: 600, marginBottom: 16,
            border: "1px solid var(--imrd-emerald-border)"
          }}>
            <CheckCircle2 size={16} />
            <span>{successMsg}</span>
          </div>
        )}

        <form onSubmit={handleSubmit} style={{ display: "flex", flexDirection: "column", gap: 16 }}>
          {/* Current Password */}
          <div>
            <label style={{ display: "block", fontSize: 13, fontWeight: 600, marginBottom: 6, color: "var(--text-main)" }}>
              Current Password
            </label>
            <div style={{ position: "relative" }}>
              <input
                type={showCurrent ? "text" : "password"}
                required
                value={currentPassword}
                onChange={(e) => setCurrentPassword(e.target.value)}
                placeholder="Enter current password"
                style={{
                  width: "100%", padding: "10px 42px 10px 14px",
                  borderRadius: "var(--radius-sm)", border: "1px solid var(--border-strong)",
                  fontSize: 14
                }}
              />
              <button
                type="button"
                onClick={() => setShowCurrent(!showCurrent)}
                style={{
                  position: "absolute", right: 12, top: "50%", transform: "translateY(-50%)",
                  background: "none", border: "none", cursor: "pointer", color: "var(--text-muted)"
                }}
              >
                {showCurrent ? <EyeOff size={16} /> : <Eye size={16} />}
              </button>
            </div>
          </div>

          {/* New Password */}
          <div>
            <label style={{ display: "block", fontSize: 13, fontWeight: 600, marginBottom: 6, color: "var(--text-main)" }}>
              New Password
            </label>
            <div style={{ position: "relative" }}>
              <input
                type={showNew ? "text" : "password"}
                required
                value={newPassword}
                onChange={(e) => setNewPassword(e.target.value)}
                placeholder="Minimum 12 characters"
                style={{
                  width: "100%", padding: "10px 42px 10px 14px",
                  borderRadius: "var(--radius-sm)", border: "1px solid var(--border-strong)",
                  fontSize: 14
                }}
              />
              <button
                type="button"
                onClick={() => setShowNew(!showNew)}
                style={{
                  position: "absolute", right: 12, top: "50%", transform: "translateY(-50%)",
                  background: "none", border: "none", cursor: "pointer", color: "var(--text-muted)"
                }}
              >
                {showNew ? <EyeOff size={16} /> : <Eye size={16} />}
              </button>
            </div>

            {/* Strength meter */}
            {newPassword.length > 0 && (
              <div style={{ marginTop: 8 }}>
                <div style={{ display: "flex", justifyContent: "space-between", fontSize: 11, fontWeight: 600, marginBottom: 4 }}>
                  <span>Password Strength</span>
                  <span style={{ color: strengthColor }}>{strengthLevel}</span>
                </div>
                <div style={{ height: 4, background: "#e2e8f0", borderRadius: 2, overflow: "hidden" }}>
                  <div style={{
                    width: `${(validCount / 5) * 100}%`,
                    height: "100%",
                    background: strengthColor,
                    transition: "width 0.2s ease"
                  }} />
                </div>
              </div>
            )}
          </div>

          {/* Confirm Password */}
          <div>
            <label style={{ display: "block", fontSize: 13, fontWeight: 600, marginBottom: 6, color: "var(--text-main)" }}>
              Confirm New Password
            </label>
            <input
              type="password"
              required
              value={confirmPassword}
              onChange={(e) => setConfirmPassword(e.target.value)}
              placeholder="Confirm new password"
              style={{
                width: "100%", padding: "10px 14px",
                borderRadius: "var(--radius-sm)", border: "1px solid var(--border-strong)",
                fontSize: 14
              }}
            />
          </div>

          {/* Policy Checklist */}
          <div style={{ background: "var(--surface-light)", padding: 12, borderRadius: "var(--radius-sm)", fontSize: 11 }}>
            <div style={{ fontWeight: 700, color: "var(--text-muted)", marginBottom: 6 }}>Institutional Security Policy:</div>
            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 6 }}>
              <div style={{ color: checks.length ? "var(--imrd-emerald)" : "var(--text-muted)", display: "flex", alignItems: "center", gap: 4 }}>
                {checks.length ? "✓" : "○"} Min 12 characters
              </div>
              <div style={{ color: checks.upper ? "var(--imrd-emerald)" : "var(--text-muted)", display: "flex", alignItems: "center", gap: 4 }}>
                {checks.upper ? "✓" : "○"} Uppercase letter (A-Z)
              </div>
              <div style={{ color: checks.lower ? "var(--imrd-emerald)" : "var(--text-muted)", display: "flex", alignItems: "center", gap: 4 }}>
                {checks.lower ? "✓" : "○"} Lowercase letter (a-z)
              </div>
              <div style={{ color: checks.number ? "var(--imrd-emerald)" : "var(--text-muted)", display: "flex", alignItems: "center", gap: 4 }}>
                {checks.number ? "✓" : "○"} Number (0-9)
              </div>
              <div style={{ color: checks.special ? "var(--imrd-emerald)" : "var(--text-muted)", display: "flex", alignItems: "center", gap: 4 }}>
                {checks.special ? "✓" : "○"} Special symbol (!@#$)
              </div>
              <div style={{ color: checks.matches ? "var(--imrd-emerald)" : "var(--text-muted)", display: "flex", alignItems: "center", gap: 4 }}>
                {checks.matches ? "✓" : "○"} Passwords match
              </div>
            </div>
          </div>

          <div style={{ display: "flex", justifyContent: "flex-end", gap: 12, marginTop: 8 }}>
            <button
              type="button"
              className="btn btn-secondary"
              onClick={onClose}
            >
              Cancel
            </button>
            <button
              type="submit"
              className="btn btn-navy"
              disabled={loading}
            >
              {loading ? "Updating..." : "Update Password"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};
export default ChangePasswordModal;

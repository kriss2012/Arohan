import React, { useState, useEffect, useRef } from "react";
import { 
  Shield, CheckCircle2, AlertCircle, ArrowLeft, Eye, EyeOff, 
  Lock, Mail, KeyRound, Clock, UserCheck, RefreshCw 
} from "lucide-react";
import { api } from "../services/api";
import { UserSummary } from "../types";

interface AuthScreenProps {
  onLoginSuccess: (user: UserSummary) => void;
}

type AuthPhase = "CHECK_EMAIL" | "VERIFY_OTP" | "CREATE_PASSWORD" | "PASSWORD_LOGIN" | "FORGOT_PASSWORD";

export const AuthScreen: React.FC<AuthScreenProps> = ({ onLoginSuccess }) => {
  const [phase, setPhase] = useState<AuthPhase>("CHECK_EMAIL");
  const [email, setEmail] = useState<string>("");
  const [maskedEmail, setMaskedEmail] = useState<string>("");
  const [otpDigits, setOtpDigits] = useState<string[]>(["", "", "", "", "", ""]);
  const [setupToken, setSetupToken] = useState<string>("");
  const [password, setPassword] = useState<string>("");
  const [confirmPassword, setConfirmPassword] = useState<string>("");
  const [showPassword, setShowPassword] = useState<boolean>(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState<boolean>(false);
  const [resetCode, setResetCode] = useState<string>("");
  
  // UX & Error States
  const [loading, setLoading] = useState<boolean>(false);
  const [errorMsg, setErrorMsg] = useState<string>("");
  const [successMsg, setSuccessMsg] = useState<string>("");
  const [cooldown, setCooldown] = useState<number>(0);

  const otpInputRefs = useRef<(HTMLInputElement | null)[]>([]);

  // Cooldown timer ticker
  useEffect(() => {
    if (cooldown > 0) {
      const timer = setTimeout(() => setCooldown(cooldown - 1), 1000);
      return () => clearTimeout(timer);
    }
  }, [cooldown]);

  // Password Policy Analysis
  const hasMinLength = password.length >= 12;
  const hasUppercase = /[A-Z]/.test(password);
  const hasLowercase = /[a-z]/.test(password);
  const hasNumber = /[0-9]/.test(password);
  const hasSpecial = /[!@#$%^&*(),.?":{}|<>]/.test(password);
  const passwordsMatch = password.length > 0 && password === confirmPassword;

  const getStrengthScore = (): { score: number; label: string; color: string } => {
    let score = 0;
    if (hasMinLength) score += 2;
    if (hasUppercase) score += 1;
    if (hasLowercase) score += 1;
    if (hasNumber) score += 1;
    if (hasSpecial) score += 1;

    if (score <= 2) return { score: 25, label: "Weak", color: "#ef4444" };
    if (score <= 4) return { score: 50, label: "Fair", color: "#f59e0b" };
    if (score === 5) return { score: 75, label: "Good", color: "#3b82f6" };
    return { score: 100, label: "Strong", color: "#10b981" };
  };

  const strength = getStrengthScore();

  // 1. Submit Email Check
  const handleCheckEmail = async (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    if (!email || !email.includes("@")) {
      setErrorMsg("Please enter a valid institutional email address.");
      return;
    }

    setLoading(true);
    setErrorMsg("");
    setSuccessMsg("");

    try {
      const res = await api.checkEmail(email.trim().toLowerCase());
      setMaskedEmail(res.masked_email || email);

      if (res.status === "FIRST_TIME_SETUP") {
        setPhase("VERIFY_OTP");
        setCooldown(60);
        setSuccessMsg(res.message);
      } else if (res.status === "ACTIVE_ACCOUNT") {
        setPhase("PASSWORD_LOGIN");
      } else {
        setErrorMsg(res.message);
      }
    } catch (err: any) {
      setErrorMsg(err.message || "Unable to verify email authorization.");
    } finally {
      setLoading(false);
    }
  };

  // 2. OTP Input Handler
  const handleOtpChange = (index: number, val: string) => {
    const cleaned = val.replace(/\D/g, "");
    if (!cleaned) {
      const newDigits = [...otpDigits];
      newDigits[index] = "";
      setOtpDigits(newDigits);
      return;
    }

    // Handle paste
    if (cleaned.length > 1) {
      const newDigits = [...otpDigits];
      for (let i = 0; i < 6 && i < cleaned.length; i++) {
        newDigits[i] = cleaned[i];
      }
      setOtpDigits(newDigits);
      otpInputRefs.current[Math.min(5, cleaned.length)]?.focus();
      return;
    }

    const newDigits = [...otpDigits];
    newDigits[index] = cleaned[0];
    setOtpDigits(newDigits);

    if (index < 5) {
      otpInputRefs.current[index + 1]?.focus();
    }
  };

  const handleOtpKeyDown = (index: number, e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === "Backspace" && !otpDigits[index] && index > 0) {
      otpInputRefs.current[index - 1]?.focus();
    }
  };

  // 3. Verify OTP
  const handleVerifyOtp = async (e: React.FormEvent) => {
    e.preventDefault();
    const fullCode = otpDigits.join("");
    if (fullCode.length !== 6) {
      setErrorMsg("Please enter all 6 digits of the verification code.");
      return;
    }

    setLoading(true);
    setErrorMsg("");

    try {
      const res = await api.verifyCode(email.trim().toLowerCase(), fullCode);
      setSetupToken(res.setup_token);
      setSuccessMsg("✓ Email verified successfully. Please create your secure password.");
      setPhase("CREATE_PASSWORD");
    } catch (err: any) {
      setErrorMsg(err.message || "Invalid verification code.");
    } finally {
      setLoading(false);
    }
  };

  // Resend OTP
  const handleResendOtp = async () => {
    if (cooldown > 0) return;
    setLoading(true);
    setErrorMsg("");

    try {
      await api.sendCode(email.trim().toLowerCase());
      setCooldown(60);
      setSuccessMsg("A new verification code has been dispatched to your email.");
    } catch (err: any) {
      setErrorMsg(err.message || "Failed to resend code.");
    } finally {
      setLoading(false);
    }
  };

  // 4. Create Password
  const handleCreatePassword = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!passwordsMatch) {
      setErrorMsg("Passwords do not match.");
      return;
    }
    if (!hasMinLength || !hasUppercase || !hasLowercase || !hasNumber || !hasSpecial) {
      setErrorMsg("Please ensure your password satisfies all security criteria.");
      return;
    }

    setLoading(true);
    setErrorMsg("");

    try {
      const res = await api.setupPassword(setupToken, password, confirmPassword);
      setSuccessMsg("✓ Account secured successfully! Welcome to the system.");
      setTimeout(() => {
        onLoginSuccess(res.user);
      }, 800);
    } catch (err: any) {
      setErrorMsg(err.message || "Failed to create password.");
    } finally {
      setLoading(false);
    }
  };

  // 5. Returning User Password Login
  const handlePasswordLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!password) {
      setErrorMsg("Please enter your password.");
      return;
    }

    setLoading(true);
    setErrorMsg("");

    try {
      const res = await api.login(email.trim().toLowerCase(), password);
      onLoginSuccess(res.user);
    } catch (err: any) {
      setErrorMsg(err.message || "Incorrect email or password.");
    } finally {
      setLoading(false);
    }
  };

  // 6. Request Forgot Password
  const handleForgotPassword = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!email) {
      setErrorMsg("Please enter your email.");
      return;
    }

    setLoading(true);
    setErrorMsg("");

    try {
      const res = await api.forgotPassword(email.trim().toLowerCase());
      setSuccessMsg(res.message);
    } catch (err: any) {
      setErrorMsg(err.message || "Failed to process password reset.");
    } finally {
      setLoading(false);
    }
  };

  // 7. Submit Reset Password
  const handleResetPassword = async (e: React.FormEvent) => {
    e.preventDefault();
    if (resetCode.length !== 6) {
      setErrorMsg("Please enter the 6-digit reset code from your email.");
      return;
    }
    if (!passwordsMatch) {
      setErrorMsg("Passwords do not match.");
      return;
    }
    if (!hasMinLength) {
      setErrorMsg("Password must be at least 12 characters long.");
      return;
    }

    setLoading(true);
    setErrorMsg("");

    try {
      const res = await api.resetPassword(email.trim().toLowerCase(), resetCode, password, confirmPassword);
      setSuccessMsg(res.message);
      setPhase("PASSWORD_LOGIN");
      setPassword("");
      setConfirmPassword("");
    } catch (err: any) {
      setErrorMsg(err.message || "Failed to reset password.");
    } finally {
      setLoading(false);
    }
  };

  // Shortcut for testing persona
  const quickPickPersona = (pEmail: string) => {
    setEmail(pEmail);
    setErrorMsg("");
    setSuccessMsg("");
  };

  return (
    <div className="auth-wrapper" style={{
      minHeight: "100vh",
      display: "flex",
      alignItems: "center",
      justifyContent: "center",
      background: "radial-gradient(circle at top, #1a365d 0%, #0a192f 100%)",
      padding: "clamp(12px, 3vw, 20px)",
      position: "relative",
      overflow: "hidden"
    }}>
      {/* Ambient Institutional Watermark */}
      <div 
        className="app-watermark-fixed" 
        style={{ opacity: 0.18 }} 
        title="LOGIC LEGEND • Ideas Today • Impact Tomorrow" 
      />

      <div className="auth-card" style={{
        width: "100%",
        maxWidth: "460px",
        background: "#ffffff",
        borderRadius: "12px",
        boxShadow: "0 20px 25px -5px rgba(0,0,0,0.2), 0 10px 10px -5px rgba(0,0,0,0.1)",
        overflow: "hidden",
        border: "1px solid rgba(226, 232, 240, 0.8)",
        zIndex: 1
      }}>
        {/* Institutional Top Header */}
        <div style={{
          background: "#0f2b48",
          padding: "20px 16px 16px 16px",
          textAlign: "center",
          color: "#ffffff",
          display: "flex",
          flexDirection: "column",
          alignItems: "center"
        }}>
          <img 
            src="/logo.png" 
            alt="AROHAN Logo" 
            style={{
              width: "64px",
              height: "64px",
              objectFit: "contain",
              borderRadius: "14px",
              boxShadow: "0 8px 16px rgba(0, 0, 0, 0.35)",
              marginBottom: "10px",
              border: "2px solid rgba(56, 189, 248, 0.3)"
            }}
          />
          <div style={{ display: "inline-flex", alignItems: "center", gap: "8px", background: "rgba(255,255,255,0.1)", padding: "4px 12px", borderRadius: "20px", fontSize: "11px", fontWeight: 600, letterSpacing: "1px", marginBottom: "6px" }}>
            <Shield size={13} color="#38bdf8" /> IMRD SHIRPUR
          </div>
          <h1 style={{ margin: "0 0 4px 0", fontSize: "clamp(16px, 4vw, 18px)", fontWeight: 700, letterSpacing: "0.5px" }}>
            AROHAN • ISDP CAMPUS LMS
          </h1>
          <p style={{ margin: 0, fontSize: "11px", color: "#94a3b8", lineHeight: 1.4 }}>
            AI-Powered Personalized Career & Skill Development Platform
          </p>
        </div>

        <div style={{ padding: "clamp(20px, 4vw, 32px) clamp(16px, 3.5vw, 28px)" }}>
          {/* Notifications */}
          {errorMsg && (
            <div style={{
              display: "flex",
              alignItems: "flex-start",
              gap: "10px",
              background: "#fef2f2",
              border: "1px solid #fecaca",
              color: "#991b1b",
              padding: "12px 14px",
              borderRadius: "8px",
              fontSize: "13px",
              marginBottom: "20px",
              lineHeight: 1.4
            }}>
              <AlertCircle size={18} style={{ flexShrink: 0, marginTop: "2px" }} />
              <div>{errorMsg}</div>
            </div>
          )}

          {successMsg && (
            <div style={{
              display: "flex",
              alignItems: "flex-start",
              gap: "10px",
              background: "#f0fdf4",
              border: "1px solid #bbf7d0",
              color: "#166534",
              padding: "12px 14px",
              borderRadius: "8px",
              fontSize: "13px",
              marginBottom: "20px",
              lineHeight: 1.4
            }}>
              <CheckCircle2 size={18} style={{ flexShrink: 0, marginTop: "2px" }} />
              <div>{successMsg}</div>
            </div>
          )}

          {/* PHASE 1: CHECK EMAIL */}
          {phase === "CHECK_EMAIL" && (
            <div>
              <div style={{ marginBottom: "24px" }}>
                <h2 style={{ margin: "0 0 6px 0", fontSize: "20px", color: "#0f2b48", fontWeight: 700 }}>
                  Welcome
                </h2>
                <p style={{ margin: 0, fontSize: "13px", color: "#64748b" }}>
                  Sign in using your administrator-authorized institutional email.
                </p>
              </div>

              <form onSubmit={handleCheckEmail}>
                <div style={{ marginBottom: "20px" }}>
                  <label style={{ display: "block", fontSize: "12px", fontWeight: 600, color: "#334155", marginBottom: "6px" }}>
                    Institutional Email Address
                  </label>
                  <div style={{ position: "relative" }}>
                    <Mail size={16} color="#94a3b8" style={{ position: "absolute", left: "12px", top: "50%", transform: "translateY(-50%)" }} />
                    <input 
                      type="email"
                      required
                      placeholder="username@imrd.ac.in"
                      value={email}
                      onChange={(e) => setEmail(e.target.value)}
                      style={{
                        width: "100%",
                        boxSizing: "border-box",
                        padding: "11px 12px 11px 38px",
                        border: "1px solid #cbd5e1",
                        borderRadius: "6px",
                        fontSize: "14px",
                        outline: "none",
                        color: "#0f172a"
                      }}
                    />
                  </div>
                </div>

                <button
                  type="submit"
                  disabled={loading}
                  style={{
                    width: "100%",
                    padding: "12px",
                    background: "#0f2b48",
                    color: "#ffffff",
                    border: "none",
                    borderRadius: "6px",
                    fontSize: "14px",
                    fontWeight: 600,
                    cursor: loading ? "not-allowed" : "pointer",
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "center",
                    gap: "8px",
                    transition: "background 0.2s"
                  }}
                >
                  {loading ? "Checking Authorization..." : "Continue"}
                </button>
              </form>

              {/* Fast Evaluation Persona Switcher */}
              <div style={{ marginTop: "28px", paddingTop: "20px", borderTop: "1px dashed #e2e8f0" }}>
                <div style={{ fontSize: "11px", fontWeight: 600, color: "#64748b", textTransform: "uppercase", letterSpacing: "0.5px", marginBottom: "10px" }}>
                  Institutional Demo Profiles:
                </div>
                <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "8px" }}>
                  <button 
                    type="button"
                    onClick={() => quickPickPersona("rahul@imrd.ac.in")}
                    style={{ padding: "6px 8px", fontSize: "11px", background: "#f8fafc", border: "1px solid #e2e8f0", borderRadius: "4px", color: "#0f2b48", cursor: "pointer", textAlign: "left" }}
                  >
                    <strong>Rahul Patil</strong> (1st Time Setup)
                  </button>
                  <button 
                    type="button"
                    onClick={() => quickPickPersona("student1@imrd.ac.in")}
                    style={{ padding: "6px 8px", fontSize: "11px", background: "#f8fafc", border: "1px solid #e2e8f0", borderRadius: "4px", color: "#0f2b48", cursor: "pointer", textAlign: "left" }}
                  >
                    <strong>Rohan Patil</strong> (Active Student)
                  </button>
                  <button 
                    type="button"
                    onClick={() => quickPickPersona("faculty1@imrd.ac.in")}
                    style={{ padding: "6px 8px", fontSize: "11px", background: "#f8fafc", border: "1px solid #e2e8f0", borderRadius: "4px", color: "#0f2b48", cursor: "pointer", textAlign: "left" }}
                  >
                    <strong>Prof. S. N. Patil</strong> (Faculty)
                  </button>
                  <button 
                    type="button"
                    onClick={() => quickPickPersona("admin@imrd.ac.in")}
                    style={{ padding: "6px 8px", fontSize: "11px", background: "#f8fafc", border: "1px solid #e2e8f0", borderRadius: "4px", color: "#0f2b48", cursor: "pointer", textAlign: "left" }}
                  >
                    <strong>Campus Admin</strong> (Admin)
                  </button>
                </div>
              </div>
            </div>
          )}

          {/* PHASE 2: VERIFY OTP */}
          {phase === "VERIFY_OTP" && (
            <div>
              <button 
                type="button"
                onClick={() => { setPhase("CHECK_EMAIL"); setErrorMsg(""); }}
                style={{ display: "inline-flex", alignItems: "center", gap: "6px", background: "none", border: "none", color: "#64748b", fontSize: "12px", cursor: "pointer", padding: 0, marginBottom: "16px" }}
              >
                <ArrowLeft size={14} /> Use a different email
              </button>

              <div style={{ textAlign: "center", marginBottom: "24px" }}>
                <div style={{ display: "inline-flex", alignItems: "center", justifyContent: "center", width: "48px", height: "48px", borderRadius: "24px", background: "#e0f2fe", color: "#0284c7", marginBottom: "12px" }}>
                  <KeyRound size={24} />
                </div>
                <h2 style={{ margin: "0 0 6px 0", fontSize: "18px", color: "#0f2b48", fontWeight: 700 }}>
                  Verify Your Email
                </h2>
                <p style={{ margin: 0, fontSize: "13px", color: "#64748b" }}>
                  We sent a 6-digit authentication code to:
                </p>
                <div style={{ fontWeight: 600, color: "#0f2b48", fontSize: "14px", marginTop: "4px", letterSpacing: "0.5px" }}>
                  {maskedEmail}
                </div>
              </div>

              <form onSubmit={handleVerifyOtp}>
                <div style={{ display: "flex", justifyContent: "center", gap: "clamp(4px, 1.5vw, 8px)", marginBottom: "24px", width: "100%" }}>
                  {otpDigits.map((digit, idx) => (
                    <input
                      key={idx}
                      ref={(el) => { otpInputRefs.current[idx] = el; }}
                      type="text"
                      inputMode="numeric"
                      maxLength={idx === 0 ? 6 : 1}
                      value={digit}
                      onChange={(e) => handleOtpChange(idx, e.target.value)}
                      onKeyDown={(e) => handleOtpKeyDown(idx, e)}
                      style={{
                        width: "clamp(34px, 10vw, 44px)",
                        height: "clamp(42px, 12vw, 50px)",
                        textAlign: "center",
                        fontSize: "clamp(16px, 4.5vw, 20px)",
                        fontWeight: 700,
                        border: "2px solid #cbd5e1",
                        borderRadius: "8px",
                        outline: "none",
                        color: "#0f2b48",
                        background: "#f8fafc",
                        flexShrink: 1,
                        minWidth: 0
                      }}
                    />
                  ))}
                </div>

                <button
                  type="submit"
                  disabled={loading}
                  style={{
                    width: "100%",
                    padding: "12px",
                    background: "#0f2b48",
                    color: "#ffffff",
                    border: "none",
                    borderRadius: "6px",
                    fontSize: "14px",
                    fontWeight: 600,
                    cursor: loading ? "not-allowed" : "pointer",
                    marginBottom: "16px"
                  }}
                >
                  {loading ? "Verifying..." : "Verify Email"}
                </button>

                <div style={{ textAlign: "center", fontSize: "12px", color: "#64748b" }}>
                  Didn't receive the code?{" "}
                  {cooldown > 0 ? (
                    <span style={{ fontWeight: 600, color: "#0f2b48" }}>
                      Resend code in 00:{cooldown < 10 ? `0${cooldown}` : cooldown}
                    </span>
                  ) : (
                    <button
                      type="button"
                      onClick={handleResendOtp}
                      style={{ background: "none", border: "none", color: "#0284c7", fontWeight: 600, cursor: "pointer", textDecoration: "underline", padding: 0 }}
                    >
                      Resend Code
                    </button>
                  )}
                </div>
              </form>
            </div>
          )}

          {/* PHASE 3: MANDATORY PASSWORD CREATION */}
          {phase === "CREATE_PASSWORD" && (
            <div>
              <div style={{ marginBottom: "20px" }}>
                <h2 style={{ margin: "0 0 6px 0", fontSize: "18px", color: "#0f2b48", fontWeight: 700 }}>
                  Secure Your Account
                </h2>
                <p style={{ margin: 0, fontSize: "13px", color: "#64748b" }}>
                  Your email has been verified. Create a personal password for all future logins.
                </p>
              </div>

              <form onSubmit={handleCreatePassword}>
                <div style={{ marginBottom: "16px" }}>
                  <label style={{ display: "block", fontSize: "12px", fontWeight: 600, color: "#334155", marginBottom: "6px" }}>
                    Create Password
                  </label>
                  <div style={{ position: "relative" }}>
                    <input
                      type={showPassword ? "text" : "password"}
                      required
                      placeholder="••••••••••••••••"
                      value={password}
                      onChange={(e) => setPassword(e.target.value)}
                      style={{
                        width: "100%",
                        boxSizing: "border-box",
                        padding: "10px 40px 10px 12px",
                        border: "1px solid #cbd5e1",
                        borderRadius: "6px",
                        fontSize: "14px",
                        outline: "none"
                      }}
                    />
                    <button
                      type="button"
                      onClick={() => setShowPassword(!showPassword)}
                      style={{ position: "absolute", right: "12px", top: "50%", transform: "translateY(-50%)", background: "none", border: "none", cursor: "pointer", color: "#94a3b8", padding: 0 }}
                    >
                      {showPassword ? <EyeOff size={16} /> : <Eye size={16} />}
                    </button>
                  </div>

                  {/* Password Strength Indicator */}
                  {password.length > 0 && (
                    <div style={{ marginTop: "8px" }}>
                      <div style={{ display: "flex", justifyContent: "space-between", fontSize: "11px", marginBottom: "4px" }}>
                        <span style={{ color: "#64748b" }}>Strength:</span>
                        <span style={{ color: strength.color, fontWeight: 700 }}>{strength.label}</span>
                      </div>
                      <div style={{ height: "4px", background: "#e2e8f0", borderRadius: "2px", overflow: "hidden" }}>
                        <div style={{ height: "100%", width: `${strength.score}%`, background: strength.color, transition: "all 0.3s" }} />
                      </div>
                    </div>
                  )}
                </div>

                <div style={{ marginBottom: "20px" }}>
                  <label style={{ display: "block", fontSize: "12px", fontWeight: 600, color: "#334155", marginBottom: "6px" }}>
                    Confirm Password
                  </label>
                  <div style={{ position: "relative" }}>
                    <input
                      type={showConfirmPassword ? "text" : "password"}
                      required
                      placeholder="••••••••••••••••"
                      value={confirmPassword}
                      onChange={(e) => setConfirmPassword(e.target.value)}
                      style={{
                        width: "100%",
                        boxSizing: "border-box",
                        padding: "10px 40px 10px 12px",
                        border: "1px solid #cbd5e1",
                        borderRadius: "6px",
                        fontSize: "14px",
                        outline: "none"
                      }}
                    />
                    <button
                      type="button"
                      onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                      style={{ position: "absolute", right: "12px", top: "50%", transform: "translateY(-50%)", background: "none", border: "none", cursor: "pointer", color: "#94a3b8", padding: 0 }}
                    >
                      {showConfirmPassword ? <EyeOff size={16} /> : <Eye size={16} />}
                    </button>
                  </div>
                </div>

                {/* Password Policy Checklist */}
                <div style={{ background: "#f8fafc", padding: "12px 14px", borderRadius: "6px", border: "1px solid #e2e8f0", marginBottom: "24px", fontSize: "11px" }}>
                  <div style={{ fontWeight: 600, color: "#475569", marginBottom: "6px" }}>Password requirements:</div>
                  <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "4px" }}>
                    <span style={{ color: hasMinLength ? "#16a34a" : "#94a3b8" }}>{hasMinLength ? "✓" : "○"} Min 12 characters</span>
                    <span style={{ color: hasUppercase ? "#16a34a" : "#94a3b8" }}>{hasUppercase ? "✓" : "○"} Uppercase (A-Z)</span>
                    <span style={{ color: hasLowercase ? "#16a34a" : "#94a3b8" }}>{hasLowercase ? "✓" : "○"} Lowercase (a-z)</span>
                    <span style={{ color: hasNumber ? "#16a34a" : "#94a3b8" }}>{hasNumber ? "✓" : "○"} Number (0-9)</span>
                    <span style={{ color: hasSpecial ? "#16a34a" : "#94a3b8" }}>{hasSpecial ? "✓" : "○"} Special character</span>
                    <span style={{ color: passwordsMatch ? "#16a34a" : "#94a3b8" }}>{passwordsMatch ? "✓" : "○"} Passwords match</span>
                  </div>
                </div>

                <button
                  type="submit"
                  disabled={loading}
                  style={{
                    width: "100%",
                    padding: "12px",
                    background: "#0f2b48",
                    color: "#ffffff",
                    border: "none",
                    borderRadius: "6px",
                    fontSize: "14px",
                    fontWeight: 600,
                    cursor: loading ? "not-allowed" : "pointer"
                  }}
                >
                  {loading ? "Securing Account..." : "Create Password & Activate Account"}
                </button>
              </form>
            </div>
          )}

          {/* PHASE 4: RETURNING USER PASSWORD LOGIN */}
          {phase === "PASSWORD_LOGIN" && (
            <div>
              <button 
                type="button"
                onClick={() => { setPhase("CHECK_EMAIL"); setErrorMsg(""); }}
                style={{ display: "inline-flex", alignItems: "center", gap: "6px", background: "none", border: "none", color: "#64748b", fontSize: "12px", cursor: "pointer", padding: 0, marginBottom: "16px" }}
              >
                <ArrowLeft size={14} /> Change email
              </button>

              <div style={{ marginBottom: "20px" }}>
                <h2 style={{ margin: "0 0 4px 0", fontSize: "18px", color: "#0f2b48", fontWeight: 700 }}>
                  Welcome Back
                </h2>
                <div style={{ fontSize: "13px", color: "#475569" }}>
                  Signing in as <strong>{email}</strong>
                </div>
              </div>

              <form onSubmit={handlePasswordLogin}>
                <div style={{ marginBottom: "16px" }}>
                  <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "6px" }}>
                    <label style={{ fontSize: "12px", fontWeight: 600, color: "#334155" }}>
                      Password
                    </label>
                    <button
                      type="button"
                      onClick={() => { setPhase("FORGOT_PASSWORD"); setErrorMsg(""); setSuccessMsg(""); }}
                      style={{ background: "none", border: "none", color: "#0284c7", fontSize: "12px", cursor: "pointer", padding: 0 }}
                    >
                      Forgot password?
                    </button>
                  </div>
                  <div style={{ position: "relative" }}>
                    <input
                      type={showPassword ? "text" : "password"}
                      required
                      placeholder="••••••••••••••••"
                      value={password}
                      onChange={(e) => setPassword(e.target.value)}
                      style={{
                        width: "100%",
                        boxSizing: "border-box",
                        padding: "10px 40px 10px 12px",
                        border: "1px solid #cbd5e1",
                        borderRadius: "6px",
                        fontSize: "14px",
                        outline: "none"
                      }}
                    />
                    <button
                      type="button"
                      onClick={() => setShowPassword(!showPassword)}
                      style={{ position: "absolute", right: "12px", top: "50%", transform: "translateY(-50%)", background: "none", border: "none", cursor: "pointer", color: "#94a3b8", padding: 0 }}
                    >
                      {showPassword ? <EyeOff size={16} /> : <Eye size={16} />}
                    </button>
                  </div>
                </div>

                <button
                  type="submit"
                  disabled={loading}
                  style={{
                    width: "100%",
                    padding: "12px",
                    background: "#0f2b48",
                    color: "#ffffff",
                    border: "none",
                    borderRadius: "6px",
                    fontSize: "14px",
                    fontWeight: 600,
                    cursor: loading ? "not-allowed" : "pointer"
                  }}
                >
                  {loading ? "Verifying..." : "Sign In Securely"}
                </button>
              </form>
            </div>
          )}

          {/* PHASE 5: FORGOT & RESET PASSWORD */}
          {phase === "FORGOT_PASSWORD" && (
            <div>
              <button 
                type="button"
                onClick={() => { setPhase("PASSWORD_LOGIN"); setErrorMsg(""); }}
                style={{ display: "inline-flex", alignItems: "center", gap: "6px", background: "none", border: "none", color: "#64748b", fontSize: "12px", cursor: "pointer", padding: 0, marginBottom: "16px" }}
              >
                <ArrowLeft size={14} /> Back to Sign In
              </button>

              <div style={{ marginBottom: "20px" }}>
                <h2 style={{ margin: "0 0 6px 0", fontSize: "18px", color: "#0f2b48", fontWeight: 700 }}>
                  Reset Your Password
                </h2>
                <p style={{ margin: 0, fontSize: "13px", color: "#64748b" }}>
                  Enter your email to receive a 6-digit password reset verification code.
                </p>
              </div>

              <div style={{ display: "flex", gap: "8px", marginBottom: "20px" }}>
                <input 
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="your.email@imrd.ac.in"
                  style={{ flex: 1, padding: "10px 12px", border: "1px solid #cbd5e1", borderRadius: "6px", fontSize: "13px" }}
                />
                <button
                  type="button"
                  onClick={handleForgotPassword}
                  disabled={loading}
                  style={{ padding: "10px 14px", background: "#f1f5f9", border: "1px solid #cbd5e1", borderRadius: "6px", fontSize: "12px", fontWeight: 600, cursor: "pointer" }}
                >
                  Send Code
                </button>
              </div>

              <form onSubmit={handleResetPassword}>
                <div style={{ marginBottom: "14px" }}>
                  <label style={{ display: "block", fontSize: "12px", fontWeight: 600, color: "#334155", marginBottom: "4px" }}>
                    6-Digit Reset Code
                  </label>
                  <input
                    type="text"
                    required
                    maxLength={6}
                    placeholder="123456"
                    value={resetCode}
                    onChange={(e) => setResetCode(e.target.value)}
                    style={{ width: "100%", boxSizing: "border-box", padding: "10px 12px", border: "1px solid #cbd5e1", borderRadius: "6px", fontSize: "14px" }}
                  />
                </div>

                <div style={{ marginBottom: "14px" }}>
                  <label style={{ display: "block", fontSize: "12px", fontWeight: 600, color: "#334155", marginBottom: "4px" }}>
                    New Password (Min 12 chars)
                  </label>
                  <input
                    type="password"
                    required
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    style={{ width: "100%", boxSizing: "border-box", padding: "10px 12px", border: "1px solid #cbd5e1", borderRadius: "6px", fontSize: "14px" }}
                  />
                </div>

                <div style={{ marginBottom: "20px" }}>
                  <label style={{ display: "block", fontSize: "12px", fontWeight: 600, color: "#334155", marginBottom: "4px" }}>
                    Confirm New Password
                  </label>
                  <input
                    type="password"
                    required
                    value={confirmPassword}
                    onChange={(e) => setConfirmPassword(e.target.value)}
                    style={{ width: "100%", boxSizing: "border-box", padding: "10px 12px", border: "1px solid #cbd5e1", borderRadius: "6px", fontSize: "14px" }}
                  />
                </div>

                <button
                  type="submit"
                  disabled={loading}
                  style={{
                    width: "100%",
                    padding: "12px",
                    background: "#0f2b48",
                    color: "#ffffff",
                    border: "none",
                    borderRadius: "6px",
                    fontSize: "14px",
                    fontWeight: 600,
                    cursor: loading ? "not-allowed" : "pointer"
                  }}
                >
                  {loading ? "Resetting Password..." : "Update Password & Return to Login"}
                </button>
              </form>
            </div>
          )}
        </div>

        {/* Institutional Footer */}
        <div style={{
          background: "#f8fafc",
          borderTop: "1px solid #e2e8f0",
          padding: "12px 24px",
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          fontSize: "11px",
          color: "#64748b"
        }}>
          <span>Zero-Cloud Local Campus Network</span>
          <span>AES / Argon2id Secured</span>
        </div>
      </div>
    </div>
  );
};

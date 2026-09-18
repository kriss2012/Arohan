import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from datetime import datetime, timezone
from typing import Optional

from backend.app.core.config import settings

EMAILS_STORAGE_DIR = os.path.join(os.getcwd(), "local_storage", "emails")

class EmailService:
    @staticmethod
    def ensure_email_dir():
        os.makedirs(EMAILS_STORAGE_DIR, exist_ok=True)

    @classmethod
    def _save_and_send(cls, to_email: str, subject: str, html_content: str, text_content: str) -> None:
        cls.ensure_email_dir()
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        safe_email = to_email.replace("@", "_at_").replace(".", "_")
        filename = f"{timestamp}_{safe_email}_{subject[:20].replace(' ', '_')}.html"
        filepath = os.path.join(EMAILS_STORAGE_DIR, filename)

        with open(filepath, "w", encoding="utf-8") as f:
            f.write(html_content)

        print(f"[EmailService] >>> Outgoing Email: To={to_email} | Subject='{subject}' | Stored='{filepath}'")

        # Optional SMTP delivery if environment configured
        smtp_host = os.getenv("SMTP_HOST")
        smtp_port = int(os.getenv("SMTP_PORT", "587"))
        smtp_user = os.getenv("SMTP_USER")
        smtp_pass = os.getenv("SMTP_PASSWORD")

        if smtp_host and smtp_user and smtp_pass:
            try:
                msg = MIMEMultipart("alternative")
                msg["Subject"] = subject
                msg["From"] = os.getenv("EMAIL_FROM", f"ISDP Campus <noreply@{smtp_host}>")
                msg["To"] = to_email
                msg.attach(MIMEText(text_content, "plain"))
                msg.attach(MIMEText(html_content, "html"))

                with smtplib.SMTP(smtp_host, smtp_port, timeout=5) as server:
                    server.starttls()
                    server.login(smtp_user, smtp_pass)
                    server.sendmail(msg["From"], [to_email], msg.as_string())
                print(f"[EmailService] Successfully sent via SMTP to {to_email}")
            except Exception as e:
                print(f"[EmailService] SMTP delivery skipped or failed ({e}), email archived locally.")

    @classmethod
    def send_invitation_email(cls, to_email: str, full_name: str, role_name: str) -> None:
        subject = "Your Account Has Been Authorized"
        html = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
  body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; background-color: #f1f5f9; margin: 0; padding: 30px; color: #1e293b; }}
  .container {{ max-width: 580px; margin: 0 auto; background: #ffffff; border-radius: 10px; overflow: hidden; border: 1px solid #e2e8f0; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.05); }}
  .header {{ background: #0f2b48; padding: 28px; text-align: center; color: #ffffff; }}
  .header h1 {{ margin: 0 0 6px 0; font-size: 20px; letter-spacing: 0.5px; font-weight: 700; text-transform: uppercase; }}
  .header p {{ margin: 0; font-size: 13px; color: #94a3b8; letter-spacing: 1px; }}
  .content {{ padding: 36px 32px; }}
  .greeting {{ font-size: 16px; font-weight: 600; color: #0f2b48; margin-bottom: 16px; }}
  .step-box {{ background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 8px; padding: 20px; margin: 24px 0; }}
  .step-box ol {{ margin: 0; padding-left: 20px; }}
  .step-box li {{ margin-bottom: 8px; font-size: 14px; line-height: 1.5; color: #334155; }}
  .btn-wrap {{ text-align: center; margin: 30px 0; }}
  .btn {{ background: #1a4d7c; color: #ffffff !important; padding: 14px 32px; border-radius: 6px; text-decoration: none; font-weight: 600; font-size: 14px; display: inline-block; letter-spacing: 0.5px; }}
  .footer {{ background: #f8fafc; border-top: 1px solid #e2e8f0; padding: 20px 32px; font-size: 12px; color: #64748b; text-align: center; }}
</style>
</head>
<body>
<div class="container">
  <div class="header">
    <h1>RC Patel IMRD Shirpur</h1>
    <p>Institute Student Development Platform • ISDP</p>
  </div>
  <div class="content">
    <div class="greeting">Hello {full_name},</div>
    <p style="font-size: 14px; line-height: 1.6; color: #334155;">
      An administrator has authorized your email address to access the institutional system as <strong>{role_name}</strong>.
      Your account is ready to be activated.
    </p>
    <div class="step-box">
      <strong>To securely activate your account:</strong>
      <ol>
        <li>Open the software application.</li>
        <li>Enter your authorized email address: <strong>{to_email}</strong></li>
        <li>Verify your email using the one-time authentication code.</li>
        <li>Create your personal password.</li>
      </ol>
    </div>
    <div class="btn-wrap">
      <a href="http://127.0.0.1:5173" class="btn">Activate My Account</a>
    </div>
    <p style="font-size: 13px; color: #64748b; margin-top: 24px;">
      This invitation is intended only for you. If you did not expect this invitation, please contact your institute administrator.
    </p>
  </div>
  <div class="footer">
    <strong>Secure Institutional Software</strong><br>
    This is an automated institutional message. Please do not reply.
  </div>
</div>
</body>
</html>"""
        text = f"Welcome {full_name}.\nYour email {to_email} has been authorized as {role_name}.\nOpen the software, enter your email, verify with the code, and set your password."
        cls._save_and_send(to_email, subject, html, text)

    @classmethod
    def send_verification_code_email(cls, to_email: str, full_name: str, code: str) -> None:
        subject = f"Your One-Time Authentication Code: {code}"
        html = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
  body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; background-color: #f1f5f9; margin: 0; padding: 30px; color: #1e293b; }}
  .container {{ max-width: 540px; margin: 0 auto; background: #ffffff; border-radius: 10px; overflow: hidden; border: 1px solid #e2e8f0; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.05); }}
  .header {{ background: #0f2b48; padding: 24px; text-align: center; color: #ffffff; }}
  .content {{ padding: 32px 28px; text-align: center; }}
  .code-badge {{ display: inline-block; font-size: 32px; font-weight: 800; letter-spacing: 8px; color: #0f2b48; background: #f1f5f9; border: 2px dashed #94a3b8; border-radius: 8px; padding: 14px 28px; margin: 24px 0; font-family: monospace; }}
  .warning {{ font-size: 13px; color: #64748b; line-height: 1.5; }}
  .footer {{ background: #f8fafc; border-top: 1px solid #e2e8f0; padding: 16px; font-size: 12px; color: #64748b; text-align: center; }}
</style>
</head>
<body>
<div class="container">
  <div class="header">
    <h2 style="margin:0; font-size: 18px;">Email Verification</h2>
    <p style="margin:4px 0 0 0; font-size: 12px; color: #94a3b8;">Institute Student Development Platform</p>
  </div>
  <div class="content">
    <p style="font-size: 15px; color: #334155; margin-bottom: 8px;">Hello {full_name},</p>
    <p style="font-size: 14px; color: #475569;">Use this one-time code to verify your authorized email and proceed to password setup:</p>
    <div class="code-badge">{code}</div>
    <p class="warning">
      This code will expire in <strong>10 minutes</strong>.<br>
      Do not share this code with anyone. Institutional staff will never ask for your verification code.
    </p>
  </div>
  <div class="footer">
    Secure Institutional Campus LMS • Automated Verification Service
  </div>
</div>
</body>
</html>"""
        text = f"Your verification code is: {code}. It expires in 10 minutes."
        cls._save_and_send(to_email, subject, html, text)

    @classmethod
    def send_password_reset_email(cls, to_email: str, full_name: str, reset_code: str) -> None:
        subject = "Reset Your Password - Institutional Security"
        html = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
  body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; background-color: #f1f5f9; margin: 0; padding: 30px; color: #1e293b; }}
  .container {{ max-width: 540px; margin: 0 auto; background: #ffffff; border-radius: 10px; overflow: hidden; border: 1px solid #e2e8f0; }}
  .header {{ background: #0f2b48; padding: 24px; text-align: center; color: #ffffff; }}
  .content {{ padding: 32px 28px; text-align: center; }}
  .code-badge {{ display: inline-block; font-size: 32px; font-weight: 800; letter-spacing: 8px; color: #b91c1c; background: #fef2f2; border: 2px dashed #f87171; border-radius: 8px; padding: 14px 28px; margin: 20px 0; font-family: monospace; }}
  .footer {{ background: #f8fafc; border-top: 1px solid #e2e8f0; padding: 16px; font-size: 12px; color: #64748b; text-align: center; }}
</style>
</head>
<body>
<div class="container">
  <div class="header">
    <h2 style="margin:0; font-size: 18px;">Password Reset Request</h2>
    <p style="margin:4px 0 0 0; font-size: 12px; color: #94a3b8;">Institute Student Development Platform</p>
  </div>
  <div class="content">
    <p style="font-size: 15px; color: #334155;">Hello {full_name},</p>
    <p style="font-size: 14px; color: #475569;">A request was made to reset the password for your account. Enter the 6-digit reset code below in the software to create a new password:</p>
    <div class="code-badge">{reset_code}</div>
    <p style="font-size: 13px; color: #64748b;">
      This code will expire in <strong>15 minutes</strong> and can only be used once.<br>
      If you did not request this reset, you can safely ignore this email.
    </p>
  </div>
  <div class="footer">
    Secure Institutional Campus LMS • Security Service
  </div>
</div>
</body>
</html>"""
        text = f"Your password reset code is: {reset_code}. It expires in 15 minutes."
        cls._save_and_send(to_email, subject, html, text)

    @classmethod
    def send_password_changed_email(cls, to_email: str, full_name: str) -> None:
        subject = "Security Alert: Your Password Was Changed"
        html = f"""<!DOCTYPE html>
<html>
<head><meta charset="utf-8"></head>
<body style="font-family: sans-serif; padding: 20px; background: #f8fafc;">
  <div style="max-width: 500px; margin: 0 auto; background: #fff; padding: 24px; border: 1px solid #e2e8f0; border-radius: 8px;">
    <h3 style="color: #0f2b48; margin-top:0;">Your Password Was Changed Successfully</h3>
    <p>Hello {full_name},</p>
    <p>The password for your account (<strong>{to_email}</strong>) was changed successfully. All previous sessions have been revoked.</p>
    <p style="color: #64748b; font-size: 12px;">If you did not perform this change, contact your institute administrator immediately.</p>
  </div>
</body>
</html>"""
        text = f"Hello {full_name}, your password was changed successfully."
        cls._save_and_send(to_email, subject, html, text)

# Production-Ready Authentication System Specification

## Admin-Authorized Email → One-Time Verification → Mandatory Password Setup → Normal Password Login

This document specifies the institutional authentication architecture for the Institute Student Development Platform (ISDP).

---

## 1. Zero Cloud Dependency & Institutional Privacy

The authentication engine operates entirely inside the institutional campus intranet without connecting to any external cloud provider, identity SaaS, or third-party authentication servers.

- **Zero Cloud**: No Firebase, Supabase, Auth0, Cognito, or remote database dependencies.
- **Local Database**: Local SQLite in WAL mode (`isdp_campus.db`).
- **Offline Email Storage**: Transactional emails (account invitations, 6-digit OTP codes, password reset links, security alerts) are rendered using institutional HTML templates and saved locally to `./local_storage/emails/` for campus intranet delivery or transmitted via an on-premise SMTP relay if configured.

---

## 2. Complete Authentication Flow

```
ADMIN AUTHORIZES USER
        ↓
User email is added to database (AuthorizedUser / User with password_hash = NULL)
        ↓
System sends account invitation email
        ↓
User opens software
        ↓
Enters authorized email (POST /api/v1/auth/check-email)
        ↓
System sends one-time 6-digit verification code (EmailVerificationCode)
        ↓
User enters verification code (POST /api/v1/auth/verify-code)
        ↓
Code verified & setup_token issued
        ↓
FIRST-TIME USER? (password_hash == NULL)
        ↓
MANDATORY PASSWORD CREATION (POST /api/v1/auth/setup-password)
        ↓
Password confirmation & policy validation (Min 12 chars, upper, lower, digit, symbol)
        ↓
Password securely hashed using Argon2id / bcrypt
        ↓
Account activated (is_email_verified = true, status = 'ACTIVE')
        ↓
Create secure session
        ↓
Dashboard
```

### Future Login Lifecycle:

```
User opens login page
        ↓
Enters email (POST /api/v1/auth/check-email -> ACTIVE_ACCOUNT)
        ↓
Enters password (POST /api/v1/auth/login)
        ↓
Backend verifies:
  1. User exists
  2. is_authorized == true
  3. is_active == true
  4. Account not locked (failed_login_attempts < 5)
  5. Password hash matches
        ↓
Create secure session (JWT access token + hashed refresh token)
        ↓
Dashboard
```

---

## 3. Account Lifecycle State Machine

The database distinguishes between authorized pending users and fully activated users:

| State | `is_authorized` | `is_active` | `is_email_verified` | `password_hash` | Description |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **New Authorized** | `true` | `true` | `false` | `NULL` | Pre-approved by admin; awaiting OTP & password setup. |
| **Active Account** | `true` | `true` | `true` | `<hash>` | Fully activated; logs in with email + password. |
| **Unauthorized** | `false` | `any` | `any` | `any` | Email not in allowlist; access strictly rejected. |
| **Deactivated** | `true` | `false` | `any` | `any` | Suspended by admin; active sessions immediately revoked. |
| **Locked Out** | `true` | `true` | `true` | `<hash>` | 5 failed password attempts; locked for 15 minutes. |

---

## 4. First-Time Verification Code (OTP) Security

- **Generation**: Cryptographically secure 6-digit numeric code (`secrets.randbelow(900000) + 100000`).
- **Storage**: Never stored in plaintext. Hashed with SHA-256 (`code_hash = sha256(code)`).
- **Expiration**: Exactly 10 minutes.
- **Attempt Limits**: Maximum 5 failed attempts allowed before code is permanently invalidated.
- **One-Time Use**: Code marked as `used_at = now()` immediately upon verification.
- **Invalidation**: Requesting a new code automatically invalidates all previous unused codes for that user.
- **Setup Session Token**: Upon successful verification, the backend issues a signed JWT `setup_token` (purpose: `"password_setup"`, 15-minute expiry). Password setup endpoints reject requests without a valid `setup_token`.

---

## 5. Password Policy & Hashing

- **Hashing**: Argon2id / bcrypt. Passwords are never stored in plaintext or reversible encryption.
- **Password Requirements**:
  - Minimum 12 characters.
  - At least 1 uppercase letter (`[A-Z]`).
  - At least 1 lowercase letter (`[a-z]`).
  - At least 1 numeric digit (`[0-9]`).
  - At least 1 special symbol (`[!@#$%^&*()_+\-=\[\]{}|;:,.<>?]`).
  - Blacklist rejection of common weak passwords (e.g. `Password123!`, `Admin123456!`).
- **Live Guidance**: Client UI provides a live strength indicator (Weak / Fair / Good / Strong) and policy checklist.

---

## 6. Forgot & Reset Password Flow

1. User clicks "Forgot Password" on login screen.
2. User enters authorized email address (`POST /api/v1/auth/forgot-password`).
3. Backend generates a cryptographically secure 6-digit reset token and hashes it via SHA-256 in `password_reset_tokens`.
4. Reset instructions and code are dispatched via email (`send_password_reset_email`).
5. User provides email, reset code, and new password (`POST /api/v1/auth/reset-password`).
6. On success:
   - Password hash is updated.
   - All existing user sessions are revoked (`is_revoked = true`).
   - Reset token is marked `used_at = now()`.
   - Security alert email (`send_password_changed_email`) is dispatched.

---

## 7. Admin Security Controls

Administrators with role `INSTITUTE_ADMIN` or `SUPER_ADMIN` have full account lifecycle control:

1. **Authorize User (`POST /api/v1/admin/authorized-users`)**:
   Adds an email to the allowlist and dispatches the institutional invitation email.
2. **Deactivate User (`POST /api/v1/admin/users/{id}/deactivate`)**:
   Sets `is_active = false` and immediately terminates and revokes all active user sessions.
3. **Reactivate User (`POST /api/v1/admin/users/{id}/reactivate`)**:
   Restores login permissions and resets lockout counters.
4. **Unlock User (`POST /api/v1/admin/users/{id}/unlock`)**:
   Clears failed login attempt counters and lifts the 15-minute lockout timer.
5. **Resend Invitation (`POST /api/v1/admin/users/{id}/resend-invitation`)**:
   Regenerates and redispatches activation instructions.
6. **Revoke Sessions (`POST /api/v1/admin/users/{id}/revoke-sessions`)**:
   Revokes all active refresh tokens for the specified user.

---

## 8. Audit Logging & Security Events

All critical authentication transitions are audited:
- `USER_AUTHORIZED`
- `EMAIL_VERIFICATION_REQUESTED`
- `EMAIL_VERIFICATION_SUCCESS`
- `EMAIL_VERIFICATION_FAILED`
- `PASSWORD_CREATED`
- `LOGIN_SUCCESS`
- `LOGIN_FAILED`
- `PASSWORD_RESET_REQUESTED`
- `PASSWORD_RESET_SUCCESS`
- `PASSWORD_CHANGED`
- `USER_DEACTIVATED`
- `SESSIONS_REVOKED`

Passwords, plaintext OTPs, and secrets are never written to logs.

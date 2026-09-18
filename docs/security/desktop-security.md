# Desktop Client Security Specification (Tauri / Native Shell)

## 1. Zero Trust in Client Execution Environment

The desktop software is assumed to run on student and laboratory computers where local users may possess local administrator access, debugging tools, or network proxies.
- **Rule 1: Client State is Non-Authoritative**: The desktop client is treated strictly as a rendering and input mechanism. User roles, permissions, exam timers, and scores are never decided on the client.
- **Rule 2: Zero Hardcoded Secrets**: No master API keys, database credentials, or administrative passphrases are embedded in the compiled JavaScript or native executable bundle.

---

## 2. Desktop Shell Hardening (Tauri Security Controls)

1. **Minimized Capability Permissions**:
   - The Tauri webview is denied unrestricted access to the underlying OS filesystem, command shell, and child processes.
   - Filesystem access is strictly restricted to application-scoped cache directories.
2. **Context Isolation**:
   - Frontend JavaScript executes in an isolated browsing context without direct access to Node.js or native operating system APIs.
3. **Local Storage Sanitization**:
   - Authentication tokens are stored in memory or secure credential storage (OS Credential Manager / Keychain / secure cookie).
   - Sensitive institutional documents and exam question banks are never written to permanent disk on client workstations.

---

## 3. Client Tampering Defenses

1. **Anti-Tamper Signature Verification**:
   - Official institutional desktop releases are signed using an institutional code-signing certificate.
   - Installers and offline updates distributed via campus network shares or USB media verify cryptographic SHA-256 checksums prior to execution.
2. **Server-Authoritative Clock**:
   - Exam durations and submission deadlines rely exclusively on `X-Server-Time-UTC`. Modifying the workstation's local clock has zero effect on exam expiration or deadline enforcement.

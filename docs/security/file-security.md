# File Storage & Upload Security Specification

## 1. Threat Profile for File Storage

Student and faculty file uploads (assignment briefs, homework submissions, project code archives) represent untrusted binary inputs with potential risks:
- Path traversal (`../../`) attempting to overwrite system files.
- Disguised executables (e.g. `.exe` renamed to `.pdf`) attempting server-side code execution.
- Decompression bombs / zip-slip attacks in project archives.
- File tampering and silent historical document replacement.

---

## 2. Multi-Stage Inbound Validation Pipeline

Every file uploaded to `/api/v1/files/upload` undergoes five validation gates:

```
[ UNTRUSTED UPLOAD ]
        ↓
[ GATE 1: Path & Filename Sanitization ]
Strip all directories; extract basename; reject null-byte tricks (`\x00`).
        ↓
[ GATE 2: Extension Allowlist ]
Strict check against allowed extensions:
.pdf, .docx, .pptx, .xlsx, .csv, .txt, .png, .jpg, .jpeg, .zip.
        ↓
[ GATE 3: Magic Bytes Binary Inspection ]
Inspect first bytes of binary stream:
- %PDF- → application/pdf
- PK\x03\x04 → application/zip (also docx/xlsx)
- \x89PNG\r\n\x1a\n → image/png
- \xff\xd8\xff → image/jpeg
REJECT MZ header (Windows PE) and \x7fELF header (Linux binaries).
        ↓
[ GATE 4: File Size Quotas ]
Max 25 MB per assignment document; max 50 MB per project zip.
        ↓
[ GATE 5: Non-Colliding Storage & SHA-256 Hashing ]
Generate UUID storage filename (`uuid.hex + ext`); calculate SHA-256 hash.
Save to `./local_storage/<category>/`; insert record into `files` table.
```

---

## 3. Safe Document Access & Serving

1. **No Direct Web Server Directory Listing**:
   - The `./local_storage/` root is outside the web server's static document root. Files cannot be accessed by navigating to raw file paths.
2. **Authenticated Streaming Endpoint**:
   - Downloads occur via `GET /api/v1/files/{id}/download`.
   - The server validates session token, user role, and resource ownership before streaming file chunks.
3. **Download Headers**:
   - Files are served with `Content-Disposition: attachment; filename="..."` and `X-Content-Type-Options: nosniff` to prevent browser script execution.
   - Cryptographic SHA-256 checksum is provided in the `X-Checksum-SHA256` header.

---

## 4. Immutable File Versioning

Replacing an existing document does not overwrite the physical file:
- The previous file is preserved and indexed in `file_versions` with `version_number`, `checksum_sha256`, and `uploaded_by`.
- The new document receives a new UUID on disk and an incremented version number.

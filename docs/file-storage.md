# Local File Storage & Security Architecture

## 1. Local Storage Structure
Files are stored directly on the local filesystem under the institute-configured directory (`STORAGE_ROOT = ./local_storage`), completely isolated from the web root:
```
STORAGE_ROOT/
├── assignments/
├── submissions/
├── resources/
├── backups/
└── temp/
```

## 2. File Upload Security Pipeline
When any user uploads a document (assignment brief, submission file, reading material):
1. **Magic Bytes Validation**: The first 512 bytes are inspected using file signature detection. Files disguised with fake extensions (e.g. `.exe` or `.dll` with a `.pdf` extension) are rejected with `HTTP 400 Bad Request`.
2. **Path Traversal Protection**: Filenames submitted by users are stripped and sanitized. The physical file is assigned a secure random UUID: `<category>/<uuid4>.<safe_ext>`.
3. **SHA-256 Checksum**: The cryptographic SHA-256 hash of the content is computed and stored in `files.checksum_sha256`.
4. **File Metadata Record**: Stored in `files` table with `original_filename`, `file_size`, `mime_type`, and `uploaded_by`.

## 3. File Versioning
If a faculty member replaces an assignment document:
- The previous physical file is preserved.
- An entry is recorded in `file_versions` with the prior `storage_path`, `checksum`, `version_number`, and timestamp.
- The `files` table is updated to `version = version + 1`.

## 4. Safe Download & Tamper Detection
- Files are served via `GET /api/v1/files/{file_id}/download`.
- Before streaming, the backend recalculates the SHA-256 hash of the physical disk file. If it does not match the database checksum, it flags corruption (`HTTP 500`).
- If the physical file is missing from disk, it displays a polite error without exposing local directory paths or crashing the application.
- The response sets the `X-Checksum-SHA256` header for client verification.

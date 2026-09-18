# Backup Security & 3-2-1 Institutional Storage Policy

## 1. The 3-2-1 Backup Strategy for Local Institutional Deployments

Because the platform operates without third-party cloud databases, institutional business continuity relies on a hardened, physical 3-2-1 backup strategy:

```
[ PRIMARY DATABASE & ASSETS ]
Campus Application Server (Local NVMe / SSD)
        │
        ├── Copy 1: Automated Daily Backup Bundle (Local Server Secondary Drive)
        │
        ├── Copy 2: Dedicated Institutional Network Storage (Campus NAS / Airgapped VLAN)
        │
        └── Copy 3: Weekly Offline Encrypted Media (Detached USB Drive / Vault Storage)
```

- **3 Copies**: Primary running database + 2 separate backup snapshots.
- **2 Different Storage Media**: Server local drive + external NAS or USB drive.
- **1 Air-Gapped / Offline Copy**: At least one backup media is physically detached from the network to ensure absolute ransomware resilience.

---

## 2. Backup Bundle Structure & Verification

Every backup created via `POST /api/v1/admin/backups/create` generates a structured ZIP bundle containing:
1. **`database_snapshot.sqlite`**: Consistent WAL checkpoint copy of `isdp_campus.db`.
2. **`files_archive/`**: All physical assignment briefs, student submissions, and learning resources.
3. **`manifest.json`**:
   - `backup_id` (UUID)
   - `created_at_utc` (ISO 8601)
   - `application_version`
   - `total_files` and `total_bytes`
   - `sha256_checksum` of the SQLite snapshot and all archived files.

---

## 3. Ransomware Resilience & Key Management

1. **Write-Once Media**: Campus network backup shares enforce append-only permissions for the backup service account. Standard user workstations cannot modify or delete existing backups.
2. **Encryption at Rest**: Sensitive backup archives are encrypted using AES-256 before transfer to external media.
3. **Key Separation**: Encryption keys are stored in an institute password manager or HSM and are never stored in the same folder as the `.zip` archive.

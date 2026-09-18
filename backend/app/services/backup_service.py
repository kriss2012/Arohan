import os
import json
import zipfile
import shutil
import hashlib
from datetime import datetime, timezone
from typing import Dict, Any, List
from backend.app.core.config import settings

BACKUP_ROOT = os.getenv("BACKUP_ROOT", os.path.abspath("./local_storage/backups"))
STORAGE_ROOT = os.getenv("STORAGE_ROOT", os.path.abspath("./local_storage"))

class BackupService:
    @staticmethod
    def ensure_backup_directory():
        os.makedirs(BACKUP_ROOT, exist_ok=True)

    @staticmethod
    def calculate_file_sha256(filepath: str) -> str:
        sha = hashlib.sha256()
        with open(filepath, "rb") as f:
            while chunk := f.read(65536):
                sha.update(chunk)
        return sha.hexdigest()

    @classmethod
    def create_backup(cls) -> Dict[str, Any]:
        cls.ensure_backup_directory()
        timestamp_str = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        backup_filename = f"isdp_backup_{timestamp_str}.zip"
        backup_filepath = os.path.join(BACKUP_ROOT, backup_filename)

        manifest: Dict[str, Any] = {
            "backup_version": "1.0.0",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "institution": settings.INSTITUTION_NAME,
            "database_engine": settings.DATABASE_URL.split("://")[0],
            "included_directories": ["assignments", "submissions", "resources"],
            "files": []
        }

        # Build ZIP archive
        with zipfile.ZipFile(backup_filepath, "w", zipfile.ZIP_DEFLATED) as zf:
            # 1. Archive local database file if SQLite
            if "sqlite" in settings.DATABASE_URL:
                db_filename = settings.DATABASE_URL.split("///")[-1].replace("./", "")
                if os.path.exists(db_filename):
                    zf.write(db_filename, arcname=f"database/{os.path.basename(db_filename)}")
                    manifest["files"].append({
                        "type": "database",
                        "name": os.path.basename(db_filename),
                        "sha256": cls.calculate_file_sha256(db_filename)
                    })

            # 2. Archive storage files
            for sub in ["assignments", "submissions", "resources"]:
                folder = os.path.join(STORAGE_ROOT, sub)
                if os.path.exists(folder):
                    for root, _, files in os.walk(folder):
                        for file in files:
                            abs_f = os.path.join(root, file)
                            rel_arc = os.path.relpath(abs_f, STORAGE_ROOT)
                            zf.write(abs_f, arcname=f"storage/{rel_arc}")
                            manifest["files"].append({
                                "type": "storage_file",
                                "name": rel_arc,
                                "sha256": cls.calculate_file_sha256(abs_f)
                            })

            # 3. Write manifest inside archive
            zf.writestr("manifest.json", json.dumps(manifest, indent=2))

        # Checksum of backup archive
        backup_sha = cls.calculate_file_sha256(backup_filepath)
        backup_size = os.path.getsize(backup_filepath)

        report = {
            "backup_id": f"bk-{timestamp_str}",
            "filename": backup_filename,
            "filepath": backup_filepath,
            "size_bytes": backup_size,
            "checksum_sha256": backup_sha,
            "total_files_archived": len(manifest["files"]),
            "timestamp": manifest["created_at"]
        }

        # Save report manifest next to zip
        with open(f"{backup_filepath}.json", "w") as f:
            json.dump(report, f, indent=2)

        return report

    @classmethod
    def list_backups(cls) -> List[Dict[str, Any]]:
        cls.ensure_backup_directory()
        results = []
        for file in sorted(os.listdir(BACKUP_ROOT), reverse=True):
            if file.endswith(".zip.json"):
                with open(os.path.join(BACKUP_ROOT, file), "r") as f:
                    try:
                        results.append(json.load(f))
                    except Exception:
                        pass
        return results

    @classmethod
    def verify_and_restore_backup(cls, backup_filename: str) -> Dict[str, Any]:
        cls.ensure_backup_directory()
        filepath = os.path.join(BACKUP_ROOT, backup_filename)
        if not os.path.exists(filepath):
            raise FileNotFoundError("Backup archive not found.")

        # Verify ZIP
        with zipfile.ZipFile(filepath, "r") as zf:
            if "manifest.json" not in zf.namelist():
                raise ValueError("Corrupt backup: missing manifest.json")
            manifest = json.loads(zf.read("manifest.json").decode("utf-8"))

            # Extract storage files safely (preventing path traversal)
            for item in zf.namelist():
                if item.startswith("storage/"):
                    rel = item.replace("storage/", "")
                    clean_target = os.path.normpath(os.path.join(STORAGE_ROOT, rel))
                    if not clean_target.startswith(STORAGE_ROOT):
                        raise ValueError(f"Path traversal detected in archive: {item}")
                    os.makedirs(os.path.dirname(clean_target), exist_ok=True)
                    with open(clean_target, "wb") as f:
                        f.write(zf.read(item))

        return {
            "status": "RESTORED",
            "restored_files_count": len(manifest.get("files", [])),
            "manifest": manifest
        }

    @classmethod
    def get_storage_statistics(cls) -> Dict[str, Any]:
        cls.ensure_backup_directory()
        stats = {}
        total_size = 0
        for sub in ["assignments", "submissions", "resources", "backups"]:
            path = os.path.join(STORAGE_ROOT, sub)
            sub_size = 0
            file_count = 0
            if os.path.exists(path):
                for root, _, files in os.walk(path):
                    for f in files:
                        fp = os.path.join(root, f)
                        sub_size += os.path.getsize(fp)
                        file_count += 1
            stats[sub] = {"bytes": sub_size, "files": file_count}
            total_size += sub_size

        return {
            "storage_root": STORAGE_ROOT,
            "total_bytes": total_size,
            "category_breakdown": stats
        }

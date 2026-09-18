import json
import hashlib
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc

from backend.app.models.audit import AuditLog

GENESIS_HASH = "0000000000000000000000000000000000000000000000000000000000000000"

class AuditService:
    @staticmethod
    def format_timestamp(dt: Optional[datetime]) -> str:
        if not dt:
            return ""
        if dt.tzinfo is not None:
            dt = dt.astimezone(timezone.utc).replace(tzinfo=None)
        return dt.isoformat()

    @staticmethod
    def canonical_hash(
        prev_hash: str,
        user_id: Optional[str],
        action: str,
        entity_type: Optional[str],
        entity_id: Optional[str],
        details_str: str,
        timestamp_str: str
    ) -> str:
        canonical_str = f"{prev_hash}|{user_id or ''}|{action}|{entity_type or ''}|{entity_id or ''}|{details_str}|{timestamp_str}"
        return hashlib.sha256(canonical_str.encode("utf-8")).hexdigest()

    @classmethod
    async def log_event(
        cls,
        db: AsyncSession,
        action: str,
        user_id: Optional[str] = None,
        actor_role: Optional[str] = None,
        entity_type: Optional[str] = None,
        entity_id: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        ip_address: Optional[str] = None,
        security_severity: str = "INFO"
    ) -> AuditLog:
        """
        Appends an immutable audit event with a cryptographic hash chain link.
        """
        # 1. Fetch latest record to get previous_hash
        latest_res = await db.execute(
            select(AuditLog).order_by(desc(AuditLog.timestamp), desc(AuditLog.id)).limit(1)
        )
        latest_log = latest_res.scalar_one_or_none()
        prev_hash = latest_log.record_hash if latest_log and latest_log.record_hash else GENESIS_HASH

        now = datetime.now(timezone.utc)
        now_str = cls.format_timestamp(now)
        details_json = json.dumps(details or {}, sort_keys=True)

        rec_hash = cls.canonical_hash(
            prev_hash=prev_hash,
            user_id=user_id,
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            details_str=details_json,
            timestamp_str=now_str
        )

        audit_entry = AuditLog(
            user_id=user_id,
            actor_role=actor_role,
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            details_json=details_json,
            ip_address=ip_address,
            security_severity=security_severity,
            previous_hash=prev_hash,
            record_hash=rec_hash,
            timestamp=now
        )
        db.add(audit_entry)
        await db.commit()
        await db.refresh(audit_entry)
        return audit_entry

    @classmethod
    async def verify_audit_chain(cls, db: AsyncSession) -> Dict[str, Any]:
        """
        Verifies the cryptographic integrity of the entire audit trail.
        Detects tampering, unauthorized insertions, deletions, or data modifications.
        """
        result = await db.execute(select(AuditLog).order_by(AuditLog.timestamp.asc(), AuditLog.id.asc()))
        logs = result.scalars().all()

        if not logs:
            return {
                "verified": True,
                "total_records": 0,
                "status": "EMPTY_CHAIN",
                "message": "Audit log is empty."
            }

        expected_prev_hash = GENESIS_HASH
        corrupted_records = []

        for idx, log in enumerate(logs):
            # Verify previous link
            if log.previous_hash and log.previous_hash != expected_prev_hash:
                corrupted_records.append({
                    "record_id": log.id,
                    "index": idx,
                    "action": log.action,
                    "expected_previous_hash": expected_prev_hash,
                    "actual_previous_hash": log.previous_hash,
                    "error_type": "PREVIOUS_HASH_MISMATCH"
                })

            # Verify current record hash
            timestamp_str = cls.format_timestamp(log.timestamp)
            recomputed_hash = cls.canonical_hash(
                prev_hash=log.previous_hash or GENESIS_HASH,
                user_id=log.user_id,
                action=log.action,
                entity_type=log.entity_type,
                entity_id=log.entity_id,
                details_str=log.details_json or "{}",
                timestamp_str=timestamp_str
            )

            if log.record_hash and log.record_hash != recomputed_hash:
                corrupted_records.append({
                    "record_id": log.id,
                    "index": idx,
                    "action": log.action,
                    "stored_record_hash": log.record_hash,
                    "recomputed_hash": recomputed_hash,
                    "error_type": "RECORD_CONTENT_TAMPERED"
                })

            expected_prev_hash = log.record_hash or recomputed_hash

        is_valid = len(corrupted_records) == 0
        return {
            "verified": is_valid,
            "total_records": len(logs),
            "status": "VALID_CHAIN" if is_valid else "TAMPER_DETECTED",
            "corrupted_records_count": len(corrupted_records),
            "corrupted_records": corrupted_records,
            "message": "Audit trail is cryptographically intact." if is_valid else f"Audit chain integrity failure: {len(corrupted_records)} anomalies detected."
        }

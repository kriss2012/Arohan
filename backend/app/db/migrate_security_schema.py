import sqlite3
import os

DB_PATH = os.path.join(os.getcwd(), "isdp_campus.db")

def run_migration():
    if not os.path.exists(DB_PATH):
        print("Database does not exist yet at", DB_PATH)
        return

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    def add_col_if_missing(table, col, col_def):
        cursor.execute(f"PRAGMA table_info({table})")
        cols = [row[1] for row in cursor.fetchall()]
        if col not in cols:
            print(f"Adding column {col} to {table}...")
            cursor.execute(f"ALTER TABLE {table} ADD COLUMN {col} {col_def}")

    add_col_if_missing("audit_logs", "actor_role", "VARCHAR(50)")
    add_col_if_missing("audit_logs", "security_severity", "VARCHAR(20) DEFAULT 'INFO'")
    add_col_if_missing("audit_logs", "previous_hash", "VARCHAR(64)")
    add_col_if_missing("audit_logs", "record_hash", "VARCHAR(64)")
    add_col_if_missing("results", "version", "INTEGER DEFAULT 1")

    # Also backfill any legacy audit logs that have NULL hashes
    cursor.execute("SELECT id, user_id, action, entity_type, entity_id, details_json, timestamp FROM audit_logs WHERE record_hash IS NULL ORDER BY timestamp ASC")
    rows = cursor.fetchall()
    prev = "0000000000000000000000000000000000000000000000000000000000000000"
    for r in rows:
        rid, uid, act, et, eid, det, ts = r
        import hashlib
        c_str = f"{prev}|{uid or ''}|{act}|{et or ''}|{eid or ''}|{det or '{}'}|{ts or ''}"
        rh = hashlib.sha256(c_str.encode('utf-8')).hexdigest()
        cursor.execute("UPDATE audit_logs SET previous_hash = ?, record_hash = ?, security_severity = 'INFO' WHERE id = ?", (prev, rh, rid))
        prev = rh

    conn.commit()
    conn.close()
    print(f"Schema migration and backfill completed successfully on {DB_PATH}.")

if __name__ == "__main__":
    run_migration()

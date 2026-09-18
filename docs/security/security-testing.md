# Automated Security Testing Methodology & Test Suite Reference

## 1. Security Testing Philosophy

Security is verified through automated, reproducible regression test suites executed prior to every production release. Testing focuses heavily on **negative scenarios**—actively attempting unauthorized actions, invalid payloads, parameter tampering, and corrupted states.

---

## 2. Automated Security Test Matrix

All security scenarios are codified in `backend/tests/test_master_security_suite.py` and run via `pytest`:

| Test Name | Threat Scenario | Verification Strategy | Result |
| :--- | :--- | :--- | :---: |
| `test_idor_and_privilege_escalation_protection` | Student attempts to access `/admin/users`, `/security/integrity/*`, or `/faculty/*` | Authenticate as student; assert HTTP 403 Forbidden on all privileged routes. | **PASSED** |
| `test_audit_log_cryptographic_hash_chain_and_tamper_detection` | Malicious actor modifies historical audit record directly in database | Append sequential audit events; verify chain is valid; corrupt record details; assert `verify_audit_chain` flags `TAMPER_DETECTED`. | **PASSED** |
| `test_physical_file_storage_integrity_scanner` | Disk corruption or unauthorized file overwrite | Save valid resource; verify clean check; modify physical bytes on disk; assert `scan_file_storage_integrity` catches corruption. | **PASSED** |
| `test_database_consistency_scanner` | Relational anomalies or orphan records | Run `scan_database_consistency` across users, roles, and results; assert anomaly reporting. | **PASSED** |
| `test_admin_security_endpoints_authorized` | Authorized admin accessing security monitoring | Authenticate as admin; assert HTTP 200 on `/security/dashboard` and `/security/integrity/verify-audit`. | **PASSED** |
| `test_unauthorized_email_registration_blocked` | Arbitrary public user attempting signup | Post unauthorized email to `/auth/check-email`; assert access restricted. | **PASSED** |
| `test_brute_force_lockout` | Credential stuffing / password guessing | Execute 5 consecutive failed logins; assert 15-minute lockout (HTTP 403). | **PASSED** |

---

## 3. Running Automated Security Tests

```bash
# Run the Master Security Test Suite
python -m pytest backend/tests/test_master_security_suite.py -v

# Run the Full End-to-End Suite (29 Tests)
python -m pytest backend/tests -v
```

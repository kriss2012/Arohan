from typing import List, Dict, Any, Tuple

class IntegrityService:
    """
    Manages exam environmental integrity signals without automatic guilt attribution.
    Language strictly enforced:
      - ALLOWED: Integrity Signal, Potential Anomaly, Review Recommended
      - FORBIDDEN: Cheater, Disqualified
    """

    @staticmethod
    def classify_signal(event_type: str, details: Dict[str, Any] = None) -> Tuple[str, str]:
        """
        Returns (Severity, Explanation)
        Severity levels: LOW, MEDIUM, HIGH
        """
        details = details or {}
        event = event_type.upper()

        if event in ["FOCUS_LOST", "WINDOW_BLUR"]:
            duration = details.get("duration_seconds", 0)
            if duration > 15:
                return "MEDIUM", f"Window focus lost for {duration} seconds (potential application switch)."
            return "LOW", f"Window focus briefly lost for {duration} seconds."

        if event in ["CLIPBOARD_COPY", "CLIPBOARD_PASTE"]:
            return "MEDIUM", "Clipboard copy/paste attempt detected inside locked exam viewport."

        if event in ["FULLSCREEN_EXIT"]:
            return "MEDIUM", "Fullscreen kiosk mode was exited by the candidate."

        if event in ["UNAUTHORIZED_PROCESS", "BLOCKED_APP_LAUNCH"]:
            app_name = details.get("process_name", "unauthorized application")
            return "HIGH", f"Attempted launch of background process: {app_name}."

        if event in ["PACKAGE_TAMPER", "INTEGRITY_HASH_MISMATCH"]:
            return "HIGH", "Encrypted exam bundle signature or hash validation failed."

        if event in ["ANOMALY_TIME", "UNUSUAL_RESPONSE_SPEED"]:
            return "MEDIUM", "Consecutive questions answered in under 2 seconds (unusual response pattern)."

        return "LOW", f"Environmental event noted: {event_type}."

    @staticmethod
    def detect_response_time_anomaly(recent_response_times: List[float]) -> bool:
        """
        Flags if candidate answers >= 5 consecutive questions in < 2.0 seconds each.
        """
        if len(recent_response_times) < 5:
            return False
        
        last_five = recent_response_times[-5:]
        return all(t < 2.0 for t in last_five)

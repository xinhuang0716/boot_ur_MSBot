"""JSON-backed feedback store."""

import json
import uuid
from datetime import datetime, timezone
from pathlib import Path

FEEDBACK_FILE = Path("log/feedback.json")


def save_feedback(response_id: str, user_id: str, rating: str, comment: str = "") -> None:
    records: list = []
    FEEDBACK_FILE.parent.mkdir(parents=True, exist_ok=True)
    try:
        records = json.loads(FEEDBACK_FILE.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        records = []

    records.append({
        "id": str(uuid.uuid4()),
        "response_id": response_id,
        "user_id": user_id,
        "rating": rating,
        "comment": comment,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    })

    FEEDBACK_FILE.write_text(json.dumps(records, indent=2, ensure_ascii=False), encoding="utf-8")

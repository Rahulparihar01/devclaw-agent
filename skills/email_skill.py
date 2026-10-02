"""Email management skills for DevClaw (Inbox triage, search, and replies)."""

from typing import Any, Dict, List, Optional
from skills.registry import skill


@skill(
    name="search_emails",
    description="Search local inbox emails by keyword or unread status.",
    parameters={
        "query": {"type": "string", "required": False, "default": ""},
        "unread_only": {"type": "boolean", "required": False, "default": False},
    },
)
def search_emails(memory: Any, query: str = "", unread_only: bool = False) -> List[Dict[str, Any]]:
    emails = memory.get_emails(unread_only=unread_only, query=query if query else None)
    return [
        {
            "id": e["id"],
            "sender": e["sender"],
            "subject": e["subject"],
            "snippet": e["body"][:120] + "..." if len(e["body"]) > 120 else e["body"],
            "is_read": bool(e["is_read"]),
            "received_at": e["received_at"],
        }
        for e in emails
    ]


@skill(
    name="read_email_full",
    description="Read the complete body of an email by its ID and mark it as read.",
    parameters={
        "email_id": {"type": "integer", "required": True},
    },
)
def read_email_full(memory: Any, email_id: int) -> Dict[str, Any]:
    emails = memory.get_emails()
    matched = next((e for e in emails if e["id"] == int(email_id)), None)
    if not matched:
        return {"error": f"Email with ID {email_id} not found."}
    memory.mark_email_read(int(email_id))
    return {
        "id": matched["id"],
        "sender": matched["sender"],
        "subject": matched["subject"],
        "body": matched["body"],
        "received_at": matched["received_at"],
    }


@skill(
    name="send_email",
    description="Send or draft an outgoing email to a recipient.",
    parameters={
        "to": {"type": "string", "required": True},
        "subject": {"type": "string", "required": True},
        "body": {"type": "string", "required": True},
    },
)
def send_email(memory: Any, to: str, subject: str, body: str) -> Dict[str, Any]:
    email_id = memory.send_email(to=to, subject=subject, body=body)
    return {
        "status": "SENT",
        "email_id": email_id,
        "to": to,
        "subject": subject,
        "message": f"Email successfully sent to {to}.",
    }


@skill(
    name="triage_inbox",
    description="Analyze and prioritize unread emails, highlighting urgent actions and summaries (OpenClaw TaskFlow).",
    parameters={},
)
def triage_inbox(memory: Any) -> Dict[str, Any]:
    emails = memory.get_emails()
    urgent = []
    travel = []
    newsletters = []
    sent = []

    for e in emails:
        sender = e["sender"].lower()
        subject = e["subject"].lower()
        if "me@user.local" in sender or "[sent to" in subject:
            sent.append(e)
        elif "flight" in subject or "airline" in sender or "united" in sender:
            travel.append(e)
        elif "sync" in subject or "review" in subject or "urgent" in subject or "alex" in sender:
            urgent.append(e)
        else:
            newsletters.append(e)

    return {
        "status": "TRIAGED",
        "urgent_count": len(urgent),
        "travel_count": len(travel),
        "urgent_emails": urgent,
        "travel_emails": travel,
        "newsletters": newsletters,
        "sent_count": len(sent),
    }


@skill(
    name="read_latest_email",
    description="Read the full content of the most recent email or first unread email.",
    parameters={},
)
def read_latest_email(memory: Any) -> Dict[str, Any]:
    unread = memory.get_emails(unread_only=True)
    target = unread[0] if unread else None
    if not target:
        all_emails = memory.get_emails()
        target = all_emails[0] if all_emails else None

    if not target:
        return {"error": "Inbox is empty."}

    memory.mark_email_read(target["id"])
    return {
        "id": target["id"],
        "sender": target["sender"],
        "subject": target["subject"],
        "body": target["body"],
        "received_at": target["received_at"],
    }


@skill(
    name="read_all_emails",
    description="Read the complete bodies of all emails in the inbox and mark them as read.",
    parameters={
        "unread_only": {"type": "boolean", "required": False, "default": False},
    },
)
def read_all_emails(memory: Any, unread_only: bool = False) -> List[Dict[str, Any]]:
    emails = memory.get_emails(unread_only=unread_only)
    for e in emails:
        memory.mark_email_read(e["id"])
    return [
        {
            "id": e["id"],
            "sender": e["sender"],
            "subject": e["subject"],
            "body": e["body"],
            "received_at": e["received_at"],
        }
        for e in emails
    ]


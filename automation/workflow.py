import hashlib
import re
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field, field_validator

TITLE = "AI Lead Qualification & Routing"


class Intake(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    email: str = Field(max_length=254)
    company: str = Field(min_length=1, max_length=100)
    message: str = Field(min_length=10, max_length=4000)
    budget_usd: int | None = Field(default=None, ge=0, le=1_000_000)
    consent_to_contact: bool

    @field_validator("email")
    @classmethod
    def valid_email(cls, value):
        value = value.casefold()
        if not re.fullmatch(r"[^\s@]+@[^\s@]+\.[^\s@]+", value):
            raise ValueError("invalid_email")
        return value


class Analysis(BaseModel):
    model_config = ConfigDict(extra="forbid")
    intent: Literal["sales", "support", "other"]
    summary: str = Field(min_length=1, max_length=400)
    evidence: str = Field(min_length=4, max_length=240)


class Processor:
    def __init__(self, model, store):
        self.model, self.store = model, store

    def __call__(self, payload):
        lead = Intake.model_validate(payload)
        if not lead.consent_to_contact:
            return {"skip": True, "reason": "no_contact_consent", "side_effects": 0}
        data, provenance = self.model.extract(
            "Classify intent as sales (new purchase), support (existing product problem), or other. "
            "Give a short factual summary. evidence must be an exact quote from the message.",
            lead.message, Analysis.model_json_schema())
        analysis = Analysis.model_validate(data)
        if analysis.evidence not in lead.message:
            raise ValueError("ungrounded_evidence")
        key = "lead-" + hashlib.sha256(lead.email.encode()).hexdigest()[:20]
        current = self.store.record(key)
        route = {"sales": "sales-queue", "support": "support-queue", "other": "manual-triage"}[analysis.intent]
        priority = "high" if analysis.intent == "sales" and (lead.budget_usd or 0) >= 5000 else "normal"
        record = {**(current["data"] if current else {}), **lead.model_dump(),
                  "route": route, "priority": priority, "analysis": analysis.model_dump(),
                  "reply_draft": "Thank you for your enquiry. A team member will review your request.",
                  "draft_only": True}
        return {"record_key": key, "expected_record_version": current["version"] if current else 0,
                "record": record, "action": "local_crm_route", "inference": provenance,
                "approval_required": True, "external_emails_sent": 0}

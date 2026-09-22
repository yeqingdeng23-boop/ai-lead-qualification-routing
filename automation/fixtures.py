"""Synthetic fixtures only. Reserved example domain; no real customer identity."""
def payload():
    return {"email": "alex@northstar.example", "company": "Northstar Sample Co",
            "message": "We want to buy a CRM integration for our 15-person sales team. Our budget is USD 8000.",
            "budget_usd": 8000, "consent_to_contact": True}


def seed(store):
    pass


def model_answer():
    return {"intent": "sales", "summary": "New CRM integration purchase enquiry.",
            "evidence": "We want to buy a CRM integration"}

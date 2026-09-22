import pytest
from automation.workflow import Intake, Processor
from automation.fixtures import payload, model_answer


def test_no_consent_skips_ai(store, fake_model):
    data = payload(); data["consent_to_contact"] = False
    result = Processor(fake_model, store)(data)
    assert result["skip"] and fake_model.calls == 0


def test_address_normalized_but_bad_address_rejected():
    data = payload(); data["email"] = "Alex@NORTHSTAR.example"
    assert Intake(**data).email == "alex@northstar.example"
    data["email"] = "bad@example"
    with pytest.raises(ValueError): Intake(**data)


def test_model_cannot_choose_arbitrary_route(store, fake_model):
    fake_model.answer = {**model_answer(), "intent": "send_to_attacker"}
    with pytest.raises(ValueError): Processor(fake_model, store)(payload())


def test_evidence_must_come_from_input(store, fake_model):
    fake_model.answer = {**model_answer(), "evidence": "The buyer approved a $100000 purchase."}
    with pytest.raises(ValueError): Processor(fake_model, store)(payload())


def test_high_priority_requires_input_budget(store, fake_model):
    data = payload(); data["budget_usd"] = None
    result = Processor(fake_model, store)(data)
    assert result["record"]["priority"] == "normal"

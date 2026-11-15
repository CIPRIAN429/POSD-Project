import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.models import AuthorizationRequest
from app.policies import KNOWN_ACTIONS, POLICY_VERSION, evaluate


def payload(role="STUDENT", action="course_view", **changes):
    body = {
        "subject": {"id": 7, "tenant_id": 1, "role": role, "is_active": True},
        "action": action,
        "resource": {"id": 20, "tenant_id": 1, "owner_id": 7, "state": "PUBLISHED", "kind": "course"},
        "context": {"enrollment_status": "ENROLLED", "has_participation": False},
    }
    for section, values in changes.items():
        body[section].update(values)
    return body


def decide(role="STUDENT", action="course_view", **changes):
    return evaluate(AuthorizationRequest.model_validate(payload(role, action, **changes)))


# Independent expectations, deliberately not derived from the implementation matrix.
EXPECTED_ACTIONS = {
    "STUDENT": {"dashboard", "catalog", "course_view", "material_read", "enroll", "withdraw", "my_courses"},
    "INSTRUCTOR": {"dashboard", "catalog", "course_view", "course_create", "course_manage", "material_read", "participants", "complete"},
    "ADMIN": {"dashboard", "catalog", "course_view", "course_create", "course_manage", "material_read", "participants", "complete", "users_manage", "policies_view", "audit_view"},
}


@pytest.mark.parametrize("role", ["STUDENT", "INSTRUCTOR", "ADMIN"])
@pytest.mark.parametrize("action", sorted(KNOWN_ACTIONS))
def test_role_action_matrix(role, action):
    assert decide(role, action).allowed == (action in EXPECTED_ACTIONS[role])


@pytest.mark.parametrize("role", ["STUDENT", "INSTRUCTOR", "ADMIN"])
@pytest.mark.parametrize("action", sorted(KNOWN_ACTIONS))
def test_every_action_rejects_other_organizations(role, action):
    result = decide(role, action, resource={"tenant_id": 2})
    assert not result.allowed
    assert result.reason == "TENANT_MISMATCH"


@pytest.mark.parametrize("role", ["STUDENT", "INSTRUCTOR", "ADMIN"])
@pytest.mark.parametrize("action", sorted(KNOWN_ACTIONS))
def test_every_action_rejects_inactive_accounts(role, action):
    assert decide(role, action, subject={"is_active": False}).reason == "ACCOUNT_INACTIVE"


@pytest.mark.parametrize("section", ["subject", "resource"])
def test_missing_tenant_fails_closed(section):
    assert decide("ADMIN", **{section: {"tenant_id": None}}).reason == "TENANT_REQUIRED"


@pytest.mark.parametrize("field,value", [("id", None), ("owner_id", None), ("state", None), ("state", "unknown")])
@pytest.mark.parametrize("action", ["course_view", "course_manage", "material_read", "enroll", "withdraw", "participants", "complete"])
def test_course_action_requires_resource_attributes(field, value, action):
    role = "STUDENT" if action in {"enroll", "withdraw"} else "ADMIN"
    assert decide(role, action, resource={field: value}).reason == "RESOURCE_ATTRIBUTES_REQUIRED"


@pytest.mark.parametrize("action", ["course_manage", "material_read", "participants", "complete"])
def test_instructor_must_own_course(action):
    assert decide("INSTRUCTOR", action, resource={"owner_id": 8}).reason == "COURSE_OWNER_REQUIRED"
    assert decide("ADMIN", action, resource={"owner_id": 8}).allowed


@pytest.mark.parametrize("role,state,own,participation,expected", [
    ("STUDENT", "PUBLISHED", False, False, True),
    ("STUDENT", "DRAFT", False, True, False),
    ("STUDENT", "ARCHIVED", False, False, False),
    ("STUDENT", "ARCHIVED", False, True, True),
    ("INSTRUCTOR", "PUBLISHED", False, False, True),
    ("INSTRUCTOR", "DRAFT", False, False, False),
    ("INSTRUCTOR", "DRAFT", True, False, True),
    ("INSTRUCTOR", "ARCHIVED", False, False, False),
    ("INSTRUCTOR", "ARCHIVED", True, False, True),
    ("ADMIN", "DRAFT", False, False, True),
    ("ADMIN", "ARCHIVED", False, False, True),
])
def test_course_visibility(role, state, own, participation, expected):
    assert decide(role, resource={"state": state, "owner_id": 7 if own else 8}, context={"enrollment_status": None, "has_participation": participation}).allowed == expected


@pytest.mark.parametrize("status", [None, "WAITLISTED", "CANCELLED", "ENROLLED", "COMPLETED"])
@pytest.mark.parametrize("state", ["DRAFT", "PUBLISHED", "ARCHIVED"])
def test_student_material_access(status, state):
    expected = state != "DRAFT" and status in {"ENROLLED", "COMPLETED"}
    assert decide(action="material_read", resource={"state": state}, context={"enrollment_status": status}).allowed == expected


@pytest.mark.parametrize("state", ["DRAFT", "PUBLISHED", "ARCHIVED"])
def test_enrollment_only_published(state):
    assert decide(action="enroll", resource={"state": state}).allowed == (state == "PUBLISHED")


@pytest.mark.parametrize("status", [None, "WAITLISTED", "CANCELLED", "ENROLLED", "COMPLETED"])
def test_enrollment_transitions(status):
    assert decide(action="withdraw", context={"enrollment_status": status}).allowed == (status in {"ENROLLED", "WAITLISTED"})
    assert decide("INSTRUCTOR", "complete", context={"enrollment_status": status}).allowed == (status == "ENROLLED")


def test_unknown_action_is_denied_even_for_admin():
    assert decide("ADMIN", "delete_everything").reason == "UNKNOWN_ACTION"


def test_tenant_level_actions_do_not_require_course_attributes():
    for role, action in [("STUDENT", "dashboard"), ("INSTRUCTOR", "course_create"), ("ADMIN", "users_manage")]:
        assert decide(role, action, resource={"id": None, "owner_id": None, "state": None, "kind": "tenant"}).allowed


@pytest.fixture
def client(monkeypatch):
    monkeypatch.setenv("POLICY_API_KEY", "test-internal-policy-key")
    with TestClient(app) as test_client:
        yield test_client


def test_health_is_anonymous(client):
    assert client.get("/health").json() == {"status": "ok", "version": POLICY_VERSION}


@pytest.mark.parametrize("headers", [{}, {"X-API-Key": "wrong"}])
def test_api_key_required(client, headers):
    assert client.get("/policies", headers=headers).status_code == 401
    assert client.post("/authorize", headers=headers, json=payload()).status_code == 401


def test_api_decision_and_catalog(client):
    headers = {"X-API-Key": "test-internal-policy-key"}
    response = client.post("/authorize", json=payload(), headers=headers)
    assert response.status_code == 200
    assert response.json() == {
        "allowed": True, "reason": "ACCESS_GRANTED",
        "matched_rules": ["active_account", "tenant_isolation", "role_permissions", "course_visibility"],
        "policy_version": POLICY_VERSION,
    }
    catalog = client.get("/policies", headers=headers).json()
    assert catalog["version"] == POLICY_VERSION
    assert len(catalog["policies"]) == 8
    assert {role["id"] for role in catalog["roles"]} == {"STUDENT", "INSTRUCTOR", "ADMIN"}


@pytest.mark.parametrize("mutation", [
    lambda body: body["subject"].pop("is_active"),
    lambda body: body["subject"].update(is_active="true"),
    lambda body: body["subject"].update(id=True),
    lambda body: body["subject"].update(role="SUPERADMIN"),
    lambda body: body["resource"].pop("tenant_id"),
    lambda body: body.update(allowed=True),
])
def test_invalid_untrusted_input_is_rejected(client, mutation):
    body = payload()
    mutation(body)
    response = client.post("/authorize", json=body, headers={"X-API-Key": "test-internal-policy-key"})
    assert response.status_code == 422


def test_service_cannot_start_without_key(monkeypatch):
    monkeypatch.delenv("POLICY_API_KEY", raising=False)
    with pytest.raises(RuntimeError, match="POLICY_API_KEY"):
        with TestClient(app):
            pass

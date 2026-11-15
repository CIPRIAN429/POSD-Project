# Policy service

This stateless FastAPI service evaluates explicit RBAC and ABAC rules. It has no database and no public port in the project Compose network. The Django application supplies attributes obtained from its authenticated session and database; browser input must never directly supply identity, ownership or enrollment attributes.

## HTTP interface

`GET /health` is anonymous. `GET /policies` and `POST /authorize` require the `X-API-Key` header matching `POLICY_API_KEY`. The process refuses to start without a key. The container listens on port `8001`.

Example authorization request:

```json
{
  "subject": {"id": 12, "tenant_id": 1, "role": "STUDENT", "is_active": true},
  "action": "material_read",
  "resource": {"id": 3, "tenant_id": 1, "owner_id": 6, "state": "PUBLISHED", "kind": "course"},
  "context": {"enrollment_status": "ENROLLED", "has_participation": true}
}
```

Example decision:

```json
{
  "allowed": true,
  "reason": "ACCESS_GRANTED",
  "matched_rules": ["active_account", "tenant_isolation", "role_permissions", "material_membership"],
  "policy_version": "1.0.0"
}
```

`matched_rules` names evaluated gates, including the rejecting rule for a denial. `reason` is a stable code, intended to be mapped to a friendly English message by Django. `GET /policies` returns `{version, policies: [{id, title, description}], roles: [{id, title, actions}]}`.

Unknown actions, missing tenants, inactive accounts and tenant mismatches are always denied. Unknown fields and mistyped values are rejected with HTTP 422. All course actions require course identity, owner and a recognized course state. Organization-level actions use the organization's `tenant_id` with `kind: "organization"`; course fields can be null.

The application must enforce prerequisite and seat-allocation transitions inside database transactions. A policy allow is necessary but not sufficient to perform a domain operation. Context for `complete` is the **target student's** enrollment; context for `withdraw` is the requesting student's enrollment.

## Tests

From this directory with dependencies installed:

```bash
python -m pytest -q
```

Tests cover role permissions, tenant isolation and disabled accounts across all actions, resource visibility, ownership, enrollment transitions, missing attributes, API keys and strict request validation.

"""Explicit RBAC and ABAC rules, with default deny and no dynamic evaluation."""

from .models import AuthorizationRequest, Decision

POLICY_VERSION = "1.0.0"

ROLE_ACTIONS = {
    "STUDENT": {
        "dashboard", "catalog", "course_view", "material_read", "enroll",
        "withdraw", "my_courses",
    },
    "INSTRUCTOR": {
        "dashboard", "catalog", "course_view", "course_create", "course_manage",
        "material_read", "participants", "complete",
    },
    "ADMIN": {
        "dashboard", "catalog", "course_view", "course_create", "course_manage",
        "material_read", "participants", "complete", "users_manage",
        "policies_view", "audit_view",
    },
}
KNOWN_ACTIONS = set().union(*ROLE_ACTIONS.values())
COURSE_ACTIONS = {
    "course_view", "course_manage", "material_read", "enroll", "withdraw",
    "participants", "complete",
}
OWNER_ACTIONS = {"course_manage", "material_read", "participants", "complete"}
COURSE_STATES = {"DRAFT", "PUBLISHED", "ARCHIVED"}

POLICIES = [
    {
        "id": "active_account",
        "title": "Active account required",
        "description": "Every protected operation requires an active account.",
    },
    {
        "id": "tenant_isolation",
        "title": "Organization isolation",
        "description": "The account and resource must belong to the same known organization.",
    },
    {
        "id": "role_permissions",
        "title": "Role permissions (RBAC)",
        "description": "Student, Instructor and Organization Administrator roles have explicit action permissions. All other actions are denied.",
    },
    {
        "id": "course_ownership",
        "title": "Course ownership (ABAC)",
        "description": "Instructors may manage courses, materials and participants only for their own courses. Organization administrators may manage all courses in their organization.",
    },
    {
        "id": "course_visibility",
        "title": "Course visibility (ABAC)",
        "description": "Published courses are visible within an organization. Instructors can also see their own drafts and archived courses; administrators can see all organization courses. Students can see archived courses with participation history.",
    },
    {
        "id": "material_membership",
        "title": "Protected learning materials (ABAC)",
        "description": "Students need an enrolled or completed enrollment to read materials in published or archived courses. Waitlisted and cancelled enrollments do not grant access.",
    },
    {
        "id": "published_enrollment",
        "title": "Enrollment availability (ABAC)",
        "description": "Only students may request enrollment, and only for published courses. Prerequisites, capacity and waitlist transitions are enforced transactionally by the application.",
    },
    {
        "id": "enrollment_transition",
        "title": "Enrollment transitions (ABAC)",
        "description": "Students may withdraw from enrolled or waitlisted states. Authorized instructors and administrators may mark only enrolled students as completed.",
    },
]


def policy_catalog() -> dict:
    return {
        "version": POLICY_VERSION,
        "policies": POLICIES,
        "roles": [
            {"id": role, "title": title, "actions": sorted(ROLE_ACTIONS[role])}
            for role, title in [
                ("STUDENT", "Student"),
                ("INSTRUCTOR", "Instructor"),
                ("ADMIN", "Organization Administrator"),
            ]
        ],
    }


def evaluate(request: AuthorizationRequest) -> Decision:
    """Return an explainable decision. Missing attributes never grant access."""
    subject, resource, context = request.subject, request.resource, request.context
    action = request.action
    matched: list[str] = []

    def decision(allowed: bool, reason: str, rule: str | None = None) -> Decision:
        rules = matched + ([rule] if rule and rule not in matched else [])
        return Decision(
            allowed=allowed, reason=reason, matched_rules=rules,
            policy_version=POLICY_VERSION,
        )

    if not subject.is_active:
        return decision(False, "ACCOUNT_INACTIVE", "active_account")
    matched.append("active_account")
    if subject.tenant_id is None or resource.tenant_id is None:
        return decision(False, "TENANT_REQUIRED", "tenant_isolation")
    if subject.tenant_id != resource.tenant_id:
        return decision(False, "TENANT_MISMATCH", "tenant_isolation")
    matched.append("tenant_isolation")
    if action not in KNOWN_ACTIONS:
        return decision(False, "UNKNOWN_ACTION", "role_permissions")
    if action not in ROLE_ACTIONS[subject.role]:
        return decision(False, "ROLE_NOT_PERMITTED", "role_permissions")
    matched.append("role_permissions")

    if action in COURSE_ACTIONS:
        if resource.id is None or resource.owner_id is None or resource.state not in COURSE_STATES:
            return decision(False, "RESOURCE_ATTRIBUTES_REQUIRED", "course_visibility")

    if subject.role == "INSTRUCTOR" and action in OWNER_ACTIONS:
        if resource.owner_id != subject.id:
            return decision(False, "COURSE_OWNER_REQUIRED", "course_ownership")
        matched.append("course_ownership")

    if action == "course_view":
        visible = (
            subject.role == "ADMIN"
            or resource.state == "PUBLISHED"
            or subject.role == "INSTRUCTOR" and resource.owner_id == subject.id
            or subject.role == "STUDENT" and resource.state == "ARCHIVED" and (
                context.has_participation
                or context.enrollment_status in {"ENROLLED", "COMPLETED"}
            )
        )
        if not visible:
            return decision(False, "COURSE_NOT_VISIBLE", "course_visibility")
        matched.append("course_visibility")

    if action == "material_read" and subject.role == "STUDENT":
        if resource.state not in {"PUBLISHED", "ARCHIVED"}:
            return decision(False, "COURSE_NOT_VISIBLE", "course_visibility")
        if context.enrollment_status not in {"ENROLLED", "COMPLETED"}:
            return decision(False, "ENROLLMENT_REQUIRED", "material_membership")
        matched.append("material_membership")

    if action == "enroll":
        if resource.state != "PUBLISHED":
            return decision(False, "COURSE_NOT_PUBLISHED", "published_enrollment")
        matched.append("published_enrollment")

    if action == "withdraw":
        if context.enrollment_status not in {"ENROLLED", "WAITLISTED"}:
            return decision(False, "WITHDRAWAL_NOT_AVAILABLE", "enrollment_transition")
        matched.append("enrollment_transition")

    if action == "complete":
        if context.enrollment_status != "ENROLLED":
            return decision(False, "ACTIVE_ENROLLMENT_REQUIRED", "enrollment_transition")
        matched.append("enrollment_transition")

    return decision(True, "ACCESS_GRANTED")

"""Strict, data-only input to the policy decision point."""

from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field

PositiveID = Annotated[int, Field(gt=0)]
Role = Literal["STUDENT", "INSTRUCTOR", "ADMIN"]


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)


class Subject(StrictModel):
    id: PositiveID
    tenant_id: PositiveID | None
    role: Role
    is_active: bool


class Resource(StrictModel):
    id: PositiveID | None = None
    tenant_id: PositiveID | None
    owner_id: PositiveID | None = None
    state: str | None = Field(default=None, max_length=32)
    kind: str = Field(min_length=1, max_length=64)


class Context(StrictModel):
    enrollment_status: str | None = Field(default=None, max_length=32)
    has_participation: bool = False


class AuthorizationRequest(StrictModel):
    subject: Subject
    action: str = Field(min_length=1, max_length=64)
    resource: Resource
    context: Context = Field(default_factory=Context)


class Decision(StrictModel):
    allowed: bool
    reason: str
    matched_rules: list[str]
    policy_version: str

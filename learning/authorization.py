import logging

import httpx
from django.conf import settings
from django.core.exceptions import PermissionDenied
from django.http import Http404

from .models import AuditEvent

logger = logging.getLogger(__name__)


class PolicyUnavailable(Exception):
    pass


def audit(user, action, *, course=None, resource_type=None, resource_id=None,
          allowed=True, reason='ACTION_COMPLETED', event_type='CHANGE', policy_version=''):
    if not user.organization_id:
        return
    AuditEvent.objects.create(
        organization_id=user.organization_id, actor=user, actor_name=user.username,
        action=action, resource_type=resource_type or ('course' if course else 'organization'),
        resource_id=resource_id if resource_id is not None else (course.pk if course else user.organization_id),
        allowed=allowed, reason=reason, event_type=event_type, policy_version=policy_version,
    )


def request_decision(payload):
    try:
        response = httpx.post(
            f'{settings.POLICY_URL}/authorize', json=payload,
            headers={'X-API-Key': settings.POLICY_API_KEY}, timeout=settings.POLICY_TIMEOUT,
        )
        response.raise_for_status()
        result = response.json()
        if (not isinstance(result.get('allowed'), bool)
                or not isinstance(result.get('reason'), str)
                or not isinstance(result.get('matched_rules'), list)
                or not isinstance(result.get('policy_version'), str)):
            raise ValueError('Malformed policy response')
        return result
    except (httpx.HTTPError, ValueError, TypeError, AttributeError) as exc:
        logger.warning('Policy service unavailable: %s', type(exc).__name__)
        raise PolicyUnavailable from exc


def authorize(user, action, *, course=None, enrollment=None, has_participation=False):
    if not user.organization_id:
        raise PermissionDenied('An organization account is required.')
    context = {
        'enrollment_status': enrollment.status if enrollment else None,
        'has_participation': has_participation,
    }
    payload = {
        'subject': {'id': user.pk, 'tenant_id': user.organization_id,
                    'role': user.role, 'is_active': user.is_active},
        'action': action,
        'resource': {
            'id': course.pk if course else None,
            'tenant_id': course.organization_id if course else user.organization_id,
            'owner_id': course.instructor_id if course else None,
            'state': course.status if course else None,
            'kind': 'course' if course else 'organization',
        },
        'context': context,
    }
    try:
        result = request_decision(payload)
    except PolicyUnavailable:
        audit(user, action, course=course, allowed=False, reason='POLICY_UNAVAILABLE', event_type='ACCESS')
        raise
    audit(user, action, course=course, allowed=result['allowed'], reason=result['reason'],
          policy_version=result['policy_version'], event_type='ACCESS')
    if not result['allowed']:
        if course and course.organization_id != user.organization_id:
            raise Http404('Resource not found.')
        raise PermissionDenied('Your account does not have access to this resource.')
    return result


def policy_catalog():
    try:
        response = httpx.get(f'{settings.POLICY_URL}/policies',
                            headers={'X-API-Key': settings.POLICY_API_KEY}, timeout=settings.POLICY_TIMEOUT)
        response.raise_for_status()
        data = response.json()
        if not isinstance(data.get('policies'), list) or not isinstance(data.get('version'), str):
            raise ValueError('Malformed policy catalog')
        return data
    except (httpx.HTTPError, ValueError, TypeError, AttributeError) as exc:
        raise PolicyUnavailable from exc

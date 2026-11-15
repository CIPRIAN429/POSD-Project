"""Help must remain available to users who cannot sign in or reach the policy service."""
from unittest.mock import patch

import pytest


def test_public_guide_and_download_work_without_policy_service(client):
    with patch('learning.authorization.httpx.post', side_effect=RuntimeError('Unavailable')):
        page = client.get('/guide/')
        assert page.status_code == 200
        assert b'Navigation and menu reference' in page.content
        assert b'id="troubleshooting"' in page.content
        download = client.get('/guide/download/')
        assert download.status_code == 200
        assert 'attachment;' in download['Content-Disposition']
        assert b'Navigation and menu reference' in b''.join(download.streaming_content)


@pytest.mark.django_db
@pytest.mark.parametrize('account', ['admin', 'instructor', 'student'])
def test_guide_available_for_each_role(client, school, account):
    user = school.students[0] if account == 'student' else getattr(school, account)
    client.force_login(user)
    response = client.get('/guide/')
    assert response.status_code == 200
    assert b'href="/guide/"' in response.content
    assert b'aria-current="page"' in response.content
    assert b'Beta Private Course' not in response.content

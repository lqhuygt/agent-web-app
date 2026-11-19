from unittest.mock import patch

import pytest
from django.db import OperationalError


def test_live_returns_200(client):
    response = client.get('/health/live/')
    assert response.status_code == 200


@pytest.mark.django_db
def test_ready_requires_database(client):
    response = client.get('/health/ready/')
    assert response.status_code == 200

    with patch('core.views.connection.cursor', side_effect=OperationalError('private database details')):
        response = client.get('/health/ready/')
    assert response.status_code == 503
    assert b'private database details' not in response.content

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.samples import load_sample


@pytest.fixture
def dirty():
    return load_sample('dirty')


@pytest.fixture
def clean():
    return load_sample('clean')


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setenv('LIFT_DB', str(tmp_path / 'db.sqlite'))
    with TestClient(app) as api:
        yield api

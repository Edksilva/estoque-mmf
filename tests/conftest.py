"""ETAPA 6 - Configuração dos testes: usa um banco temporário, separado do banco real."""
import os
import sys
import tempfile
from pathlib import Path

import pytest

_pasta = tempfile.mkdtemp()
os.environ["DATABASE_URL"] = f"sqlite:///{_pasta}/teste.db"
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from fastapi.testclient import TestClient  # noqa: E402

from app import security  # noqa: E402
from app.main import app  # noqa: E402


@pytest.fixture(scope="session")
def cliente():
    return TestClient(app)


def _token(cliente, login, senha):
    r = cliente.post("/api/auth/login", json={"login": login, "senha": senha})
    assert r.status_code == 200, r.text
    return {"Authorization": "Bearer " + r.json()["token"]}


@pytest.fixture
def admin(cliente):
    return _token(cliente, "manoel", "Mmf@2026")


@pytest.fixture
def vendedor(cliente):
    return _token(cliente, "vendedor", "Venda@2026")


@pytest.fixture(autouse=True)
def limpar_tentativas():
    security._tentativas.clear()
    yield
    security._tentativas.clear()

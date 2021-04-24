"""FastMSA의 API Test 기능을 테스트합니다.
"""
import pytest
from fastapi import routing

from fastmsa import FastMSA
from fastmsa.test.api import TestClient


@pytest.fixture
def client(msa: FastMSA):
    cli = TestClient(msa.app)

    yield cli

    msa.app.router.routes = []  # clear test routes


def test_hello_routes(msa: FastMSA, client: TestClient):
    @msa.app.get("/")
    async def read_hello():
        return {"msg": "hello world"}

    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"msg": "hello world"}


def test_hello_routes2(msa: FastMSA, client: TestClient):
    routes: list[routing.BaseRoute] = msa.app.router.routes

    @msa.app.get("/")
    async def read_hello():
        return {"msg": "hello world2"}

    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"msg": "hello world2"}

from fastapi import FastAPI
from fastapi.testclient import TestClient
from fastapi_testing.main import app

client = TestClient(app)

def test_read_item():
    response = client.get("/items/?skip=0&limit=2")
    assert response.status_code ==200
    assert response.json() == [{"item_name": "Foo"}, {"item_name": "Bar"}]

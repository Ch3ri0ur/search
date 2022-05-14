import app.main as main


from fastapi.testclient import TestClient
from fastapi import FastAPI, Security
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from fastapi.testclient import TestClient
from requests.auth import HTTPBasicAuth

client = TestClient(main.app)


def test_root():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {
        "message": "Hello World! Please visit /docs for more controls. Username: Bosch, Password: Bosch"
    }


def test_search_google_no_auth():
    response = client.get("/Bosch/")
    assert response.status_code == 401
    assert response.json() == {"detail": "Not authenticated"}


def test_search_google_success():
    auth = HTTPBasicAuth(username="Bosch", password="Bosch")
    response = client.get("/Bosch/", auth=auth)
    assert response.status_code == 200
    # not a stable test -> live search results might change
    assert response.json() == [
        {"url": "https://www.bosch.de/"},
        {"url": "https://www.bosch.de/produkte-und-services/"},
        {"url": "https://www.bosch.de/produkte-und-services/zuhause/"},
        {"url": "https://www.bosch.de/karriere/"},
        {"url": "https://www.bosch.de/kontakt/"},
        {"url": "http://www.bosch.de/"},
        {"url": "https://de.wikipedia.org/wiki/Datei:Bosch-logotype.svg"},
        {"url": "https://de.wikipedia.org/wiki/Robert_Bosch_GmbH"},
        {"url": "https://www.bosch.com/"},
        {"url": "https://www.bosch.com/careers/"},
    ]

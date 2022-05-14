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
    assert len(response.json()) == 10
    # [
    #     {"url": "https://www.bosch.com/"},
    #     {"url": "https://www.bosch.com/company/"},
    #     {"url": "https://www.bosch.com/careers/"},
    #     {"url": "https://www.bosch.com/products-and-services/"},
    #     {"url": "https://www.bosch.com/websites-worldwide/"},
    #     {"url": "https://www.bosch-home.com/us/"},
    #     {"url": "https://www.bosch-home.com/us/products/refrigerators"},
    #     {"url": "https://www.bosch-home.com/us/products/cooking-baking"},
    #     {"url": "https://www.bosch-home.com/us/products/dishwashers"},
    #     {"url": "https://www.bosch-home.com/us/owner-support/contact-us"},
    # ]

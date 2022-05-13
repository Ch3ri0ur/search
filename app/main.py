# MVP for authentication and authorization with Fastapi and Google custom search engine

from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials
import secrets

import httpx
import os
import json
from dotenv import load_dotenv

load_dotenv()
app = FastAPI()

# HTTPBasicCredentials for simple authentication
security = HTTPBasic()

# Secrets are stored in .env / environment variables
google_api_key = os.getenv("google_api_key")
search_engine_id = os.getenv("search_engine_id")

def get_current_username(credentials: HTTPBasicCredentials = Depends(security)):
    # Hard code credentials for MVP
    correct_username = secrets.compare_digest(credentials.username, "Bosch")
    correct_password = secrets.compare_digest(credentials.password, "Bosch")
    if not (correct_username and correct_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Basic"},
        )
    return credentials.username


# Basic route for testing
@app.get("/")
async def root():
    return {"message": "Hello World"}

@app.get("/search/{query}/")
@app.post("/search/{query}/")
def read_current_user(query: str, username: str = Depends(get_current_username)):
    # The Depends() propagates up and activates HTTPBasicCredentials
    # query is parsed from the URL

    # standard is 10 responses, which matches the requirements
    url = f"https://www.googleapis.com/customsearch/v1?key={google_api_key}&cx={search_engine_id}&q={query}"

    # The response is a JSON file
    response = httpx.get(url=url)

    # parse returned JSON to make trimming easier
    content = json.loads(response.content)

    return_obj = []

    for obj in content["items"]:
        print(f"Title: {obj['title']} URL: {obj['link']}")
        return_obj.append({"title": obj["title"], "url": obj["link"]})

    # FastAPI already transforms python objects into JSON
    return return_obj
    
    # otherwise you can do this:
    # # return to json format
    # json_obj = json.dumps(return_obj)

    # return json_obj

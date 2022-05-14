# MVP for authentication and authorization with Fastapi and Google custom search engine

from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials
import secrets


from googlesearch import search

app = FastAPI()

# HTTPBasicCredentials for simple authentication
security = HTTPBasic()


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
    return {
        "message": "Hello World! Please visit /docs for more controls. Username: Bosch, Password: Bosch"
    }


@app.get("/{query}/")
@app.post("/{query}/")
def read_current_user(query: str, username: str = Depends(get_current_username)):
    # The Depends() propagates up and activates HTTPBasicCredentials
    # query is parsed from the URL

    query_results = []

    # This method has a delay between queries (does not matter here) and scrapes the webpage
    for j in search(query, num=10, stop=10, pause=2):
        query_results.append({"url": j})

    # FastAPI already transforms python objects into JSON
    return query_results

    # otherwise you can do this:
    # # return to json format

    # return json.dumps(query_results)

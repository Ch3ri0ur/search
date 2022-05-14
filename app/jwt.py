# More fleshed out search api with authentication and authorization
# Backed by a google datastore for persistently storing the user data
# Best way to access the controls is at /docs/

from datetime import datetime, timedelta

from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.security import (
    OAuth2PasswordBearer,
    OAuth2PasswordRequestForm,
    HTTPBasic,
    HTTPBasicCredentials,
)
from fastapi.responses import HTMLResponse
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel
from google.cloud import datastore

import os
import httpx
import json
from dotenv import load_dotenv

# load secrets
load_dotenv()
google_api_key = os.getenv("google_api_key")
search_engine_id = os.getenv("search_engine_id")

if os.path.exists('"search-1652302074016-6595526c9b69.json"'):
    os.environ[
        "GOOGLE_APPLICATION_CREDENTIALS"
    ] = "search-1652302074016-6595526c9b69.json"


# to get a string like this run:
# openssl rand -hex 32
SECRET_KEY = os.getenv("secret_key")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30


# classes for pydantic (helps create the documentation)
class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    username: str | None = None


class User(BaseModel):
    username: str
    email: str | None = None
    full_name: str | None = None
    disabled: bool | None = False


class UserInDB(User):
    hashed_password: str


class UserRegister(User):
    password: str
    # Could create another class to not expose disabled


class searchResult(BaseModel):
    title: str
    url: str


class searchResults(BaseModel):
    result_list: list[searchResult]


class searchResultsJson(BaseModel):
    results: str


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

security = HTTPBasic()

app = FastAPI()

# Google Datastore client (takes ~20s to instanciate)
client = datastore.Client()


# Get user from Google datastore
def query_google_datastore(username: str):
    query = client.query(kind="users")
    query.add_filter("username", "=", username)
    results = list(query.fetch())
    if len(results) == 0:
        return None
    return results[0]


# Update user in Google datastore
def update_google_datastore(user: UserInDB):
    key = client.key("users", user.username)
    entity = datastore.Entity(key=key)
    entity.update(user.dict())
    client.put(entity)
    return 0  # could return the entity if needed


def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password):
    # could add salt here if needed
    return pwd_context.hash(password)


def get_user(username: str):
    result = query_google_datastore(username)
    if result is None:
        return None
    return UserInDB(**result)


def authenticate_user(username: str, password: str):
    user = get_user(username)
    if not user:
        return False
    if not verify_password(password, user.hashed_password):
        return False
    return user


# JWT methods (for authentication)
def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


async def get_current_user_jwt(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username)
    except JWTError:
        raise credentials_exception
    user = get_user(username=token_data.username)
    if user is None:
        raise credentials_exception
    return user


# Not necessary but has not caused problems
async def get_current_active_user_jwt(
    current_user: User = Depends(get_current_user_jwt),
):
    if current_user.disabled:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user


async def add_user(user_in: UserRegister):
    # check if user already exists
    result = query_google_datastore(user_in.username)
    if result is not None:
        # user already exists
        raise HTTPException(status_code=400, detail="User already exists")
    # create new user
    new_user = UserInDB(
        username=user_in.username,
        email=user_in.email,
        full_name=user_in.full_name,
        hashed_password=get_password_hash(user_in.password),
        disabled=False,
    )
    # add user to google datastore
    update_google_datastore(new_user)

    return 0


def get_current_username_basic(credentials: HTTPBasicCredentials = Depends(security)):
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Basic"},
        )

    is_authenticated = authenticate_user(credentials.username, credentials.password)
    if not is_authenticated:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Basic"},
        )
    return credentials.username


def query_google_search(query: str):
    url = "https://www.googleapis.com/customsearch/v1"
    params = {"key": google_api_key, "cx": search_engine_id, "q": query}
    response = httpx.get(url, params=params)
    return response.json()


# two different versions one with pydantic classes
def query_google_custom_list(query: str):
    content = query_google_search(query)
    return_obj = []
    if "items" not in content:
        # no results
        return return_obj

    for obj in content["items"]:
        # creating list of classes for pydantic
        return_obj.append(searchResult(title=obj["title"], url=obj["link"]))

    return return_obj


# and one with just a dict for json.dumps (could use JSON Compatible Encoder from Fastapi)
def query_google_custom_json(query: str):
    content = query_google_search(query)

    return_obj = []
    if "items" not in content:
        # no results
        return return_obj

    for obj in content["items"]:
        # creating list of python objects
        return_obj.append({"title": obj["title"], "url": obj["link"]})

    # create json string
    return json.dumps(return_obj)


# Open endpoint for registering new users
# Best use the /docs endpoint for this
@app.post("/register")
async def register_new_user(user_in: UserRegister):
    res = await add_user(user_in)
    if res != 0:
        raise HTTPException(status_code=400, detail="Something went wrong")

    return {"message": "User created successfully"}


# Get token for JWT
# This token can then be added to the Authorization header in the request
# Authentication: Bearer <token>
# See the /docs endpoint for more information (the curl command is displayed)
@app.post("/token", response_model=Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    user = authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}


# Endpoint to search, but authenticated with JWT
@app.post("/jwt/{query}", response_model=searchResults)
async def search_with_jwt_access_control(
    query: str, current_user: User = Depends(get_current_active_user_jwt)
):
    return searchResults(result_list=query_google_custom_list(query))


# Endpoint actually not really necessary because FastAPI already converts to JSON
@app.post("/jwt/string/{query}", response_model=str)
async def search_with_jwt_access_control_returns_string(
    query: str, current_user: User = Depends(get_current_active_user_jwt)
):
    json_obj = query_google_custom_json(query)
    return json_obj


# Use get and post method, so that it can function well in a browser
@app.get("/{query}", response_model=searchResults)
@app.post("/{query}", response_model=searchResults)
async def basic_search(
    query: str, current_user: User = Depends(get_current_username_basic)
):
    return searchResults(result_list=query_google_custom_list(query))


# Endpoint actually not really necessary because FastAPI already converts to JSON
@app.post("/string/{query}/")
async def basic_search_returns_json_string(
    query: str, user: str = Depends(get_current_username_basic)
):
    return query_google_custom_json(query)


@app.get("/", response_class=HTMLResponse)
def welcome_page():
    # Return welcome page, with links to the other endpoints and a serach box
    return """
    <html>
        <head>
            <title>Search Proxy</title>
        </head>
        <body>
            <h1>Welcome to this Search Proxy</h1>
            <p>Please visit the <a href="/docs">Documentation and API control</a> for better controls.</p>
            <p>Or use this link to get to the <a href="https://github.com/Ch3ri0ur/search">Github Repository</a></p>
            <p>Alternatively you can use the search box below to search Google. It will use BasicHTTPAuthentication.</p>
            <p>An already existing account is:</p>
            <p>Username: <b>Bosch</b></p>
            <p>Password: <b>Bosch</b></p>
            <form>
                <input id="search-query" type="text" value="Bosch">
                <input id="search-button" type="button" value="Search">
            </form>

        </body>
        <script
            type="text/javascript">
            const Button = document.querySelector('#search-button');
            const InputText = document.querySelector('#search-query');
            Button.addEventListener('click', clickButton);
            function clickButton() {
                var URL = "/" + InputText.value;
                var win = window.open(URL, '_blank');
                }
        </script>
    </html>
    """

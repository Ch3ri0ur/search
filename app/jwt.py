from datetime import datetime, timedelta

from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.security import (
    OAuth2PasswordBearer,
    OAuth2PasswordRequestForm,
    HTTPBasic,
    HTTPBasicCredentials,
)
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel
from google.cloud import datastore

import os
import httpx
import json
from dotenv import load_dotenv

load_dotenv()
google_api_key = os.getenv("google_api_key")
search_engine_id = os.getenv("search_engine_id")

if os.path.exists('"search-1652302074016-6595526c9b69.json"'):
    os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = "search-1652302074016-6595526c9b69.json"


# to get a string like this run:
# openssl rand -hex 32
SECRET_KEY = os.getenv("secret_key")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30


# # could use some sql instead
# fake_users_db = {
#     "Bosch": {
#         "username": "Bosch",
#         "full_name": "Bosch",
#         "email": "bosch@example.de",
#         "hashed_password": "$2b$12$Etq1mfl8839MXH9qO0jB9uthN6GF70I/DhPcbnlM8veqA0SfUCjrW",
#         "disabled": False,
#     },
# }



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
    # remove disabled


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

import time

def query_google_datastore(username: str):
    start_time = time.time()
    client = datastore.Client()
    query = client.query(kind="users")
    query.add_filter("username", "=", username)
    results = list(query.fetch())
    print("query_google_datastore:", time.time() - start_time)
    if len(results) == 0:
        return None
    return results[0]

def update_google_datastore(user: UserInDB):
    start_time = time.time()
    client = datastore.Client()
    key = client.key("users", user.username)
    entity = datastore.Entity(key=key)
    entity.update(user.dict())
    client.put(entity)
    print("update_google_datastore:", time.time() - start_time)
    return 0 # could return the entity if needed

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


def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


async def get_current_user(token: str = Depends(oauth2_scheme)):
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


async def get_current_active_user(current_user: User = Depends(get_current_user)):
    if current_user.disabled:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user


async def add_user(user_in: UserRegister):
    result = query_google_datastore(user_in.username)
    if result is not None:
        raise HTTPException(status_code=400, detail="User already exists")
    new_user = UserInDB(
        username=user_in.username,
        email=user_in.email,
        full_name=user_in.full_name,
        hashed_password=get_password_hash(user_in.password),
        disabled=False,
    )
    update_google_datastore(new_user)

    return 0


def get_current_username(credentials: HTTPBasicCredentials = Depends(security)):
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Basic"},
        )

    is_authenticated = authenticate_user(
        credentials.username, credentials.password
    )
    if not is_authenticated:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Basic"},
        )
    return credentials.username


def query_google_custom_list(query: str):
    url = f"https://www.googleapis.com/customsearch/v1?key={google_api_key}&cx={search_engine_id}&q={query}"
    response = httpx.get(url=url)
    content = json.loads(response.content)

    return_obj = []

    for obj in content["items"]:
        print(f"Title: {obj['title']} URL: {obj['link']}")
        return_obj.append(searchResult(title=obj["title"], url=obj["link"]))

    return return_obj


def query_google_custom_json(query: str):
    url = f"https://www.googleapis.com/customsearch/v1?key={google_api_key}&cx={search_engine_id}&q={query}"
    response = httpx.get(url=url)
    content = json.loads(response.content)

    return_obj = []

    for obj in content["items"]:
        print(f"Title: {obj['title']} URL: {obj['link']}")
        return_obj.append({"title": obj["title"], "url": obj["link"]})

    return return_obj
    json_obj = json.dumps(return_obj)
    print(json_obj)

    return json_obj


# would rather use get requests
@app.get("/search/{query}/")
@app.post("/search/{query}/")
def request(query: str, user: str = Depends(get_current_username)):
    return query_google_custom_json(query)


@app.get("/search/obj/{query}", response_model=searchResults)
@app.post("/search/obj/{query}", response_model=searchResults)
async def read_users_me(query: str, current_user: User = Depends(get_current_username)):
    return searchResults(result_list=query_google_custom_list(query))

@app.post("/register")
async def register(user_in: UserRegister):
    res = await add_user(user_in)
    if res != 0:
        raise HTTPException(status_code=400, detail="Something went wrong")

    return {"message": "User created successfully"}


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


@app.post("/jwt/search/{query}", response_model=str)
async def read_users_me(
    query: str, current_user: User = Depends(get_current_active_user)
):
    json_obj = query_google_custom_json(query)
    return {"content": json_obj}


@app.post("/jwt/search/obj/{query}", response_model=searchResults)
async def read_users_me(
    query: str, current_user: User = Depends(get_current_active_user)
):
    return searchResults(result_list=query_google_custom_list(query))

# Search Proxy 

This application exposes multiple endpoints, that allow the user to search Google. A cloud integration was added for learing purposes.


It uses [FastAPI](https://fastapi.tiangolo.com/) as a fast Framework (similar to Flask). FastAPI sanitizes the input and automaticaly creates documentation for the endpoints. For the search the Custom Search Engine API from Google was used. The application is in a CI/CD pipeline: When changes are pushed to Github a Google Task is triggerd that rebuilds the the Docker container. The container is then deployed with Google Cloud Run. The application is routed through a custom domain (wpplr.cc). 

## Search Method

The Custom Search Engine API was used, because it is not really allowed to programatically scrape Google results and it provides more information. The googlesearch library works well but only returns the URLs. It does not use any secrets and was used for the MVP.

# Where to find it

The full application can be found under [search.wpplr.cc](https://search.wpplr.cc).

An MVP of this application is at [mvp.wpplr.cc](https://mvp.wpplr.cc). 

The standard username is: **Bosch** and the password is also: **Bosch**

# How to use it

[search.wpplr.cc/Teacups](https://search.wpplr.cc/teacups) would query you to enter your credentials and then search for "Teacups". Same goes for the MVP variant.

[search.wpplr.cc/docs](https://search.wpplr.cc/docs) explains the whole API and gives access. At the top left (Authorize) you can log in. There are two methods basic (HTTPBasic) and JWT (OAuth2PasswordBearer). Username: **Bosch** , Password: **Bosch** (ignore client_id and client_secret). Basic enables the lower queries and the JWT method unlocks the /jwt/ variants (See the lock icon).

In the "docs" under "/register" and then "Try it out" a new user can be registered. Important are the username and password. Once the query is executed the return values and possible errors are displayed in the Server response section. One can also the curl request.

Once registered that new user can be used to log in. The user is persistently stored in the Google Cloud Datastore.

Once Authorized the other querys can be tested in the /docs:
- press on /jwt/{query}
- press "Try it out"
- Add a query
- press "Execute"
- The results are displayed.

The /docs also shows the way the return is structured.


### Return JSON

The search proxy returns a list of results in JSON format. The results consist of the title and URL of the target webpage.

## Run Localy

The MVP can be run directly (main.py)

``` Bash
git clone https://github.com/Ch3ri0ur/search.git
cd search

python -m venv venv

venv/Scripts/activate

pip install -r requirements.txt

uvicorn app.main:app --host 0.0.0.0 --port 8080
```
The JWT variant, the search.py file and datastore.py file depend on secrets and keys. and can be provided in a .env file.
- A google_api_key
- A search_engine_id
- A secret_key (just random numbers)
- A service account for gcloud (either gcloud logged in or a credentials.json)

These applications can also be started from the Dockerfiles. 


# Relevant files

Here the relevant files in the Folder structure.
## App Folder

The application is located in the jwt.py file.

- *search.py* the initial trails for searching Google from Python.
    - Two approaches were considered:
        - The Custom Search Engine API from Google allows directy querys and returns the detailed results in JSON format.
        - A Python library that scrapes the website directly
            - It does not have a high throughput (to not appear as a bot)
            - It only returns the URLs
- *main.py* the MVP with rudimentary autentication and hard coded passwords.
- *datastore.py* plays with the NoSQL datastore from Google.
- *jwt.py* the actual application. With authentication, userdatabase and search.

## Parent Folder

- *Dockerfile and JwtDockerfile* are the files for the MVP and the Application, it is read by the buildpipeline.
- *requirements.txt* the frozen requirements.
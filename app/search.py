# short proof of concept for a custom goolge search engine (https://www.googleapis.com/customsearch/v1)
# and the googlesearch library (https://pypi.org/project/google/ https://github.com/MarioVilas/googlesearch)
import httpx
import os
import json

# Variation 1 with Google Custom Search API

from dotenv import load_dotenv
load_dotenv('../.env')

# Secrets are necessary for the Google Custom Search API and are stored in a .env file
google_api_key = os.getenv("google_api_key")
search_engine_id = os.getenv("search_engine_id")

# The search string
query = "Bosch"

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

# return to json format
json_obj = json.dumps(return_obj, indent = 4)
print(json_obj)

# Variation 2
# only returns URLs 
from googlesearch import search

query_results = []

# This method has a delay between queries (does not matter here) and scrapes the webpage 
for j in search(query, num=10, stop=10, pause=2):
    query_results.append({"url": j})

# to json format
json_obj = json.dumps(query_results, indent = 4)
print(json_obj)


# Of interest is, that they don't match, 
# the webscraped variation takes more information into account to tailor the results (e.g. german)
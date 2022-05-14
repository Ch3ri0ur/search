from google.cloud import datastore
import os

os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "search-1652302074016-6595526c9b69.json"
datastore_client = datastore.Client()
key = datastore_client.key("users", "asdf")
task = datastore.Entity(key)
task.update(
    {
        "username": "asdf",
        "full_name": "asdfasdf",
        "email": "bsssosch@example.de",
        "hashed_password": "$2b$12$Etq1mfl8839MXH9qO0jB9uthN6GF70I/DhPcbnlM8veqA0SfUCjrW",
        "disabled": False,
    }
)
datastore_client.put(task)


docs = datastore_client.query(kind="users").fetch()
for doc in docs:
    print(doc.key.name)
    print(doc)

print("-----------------------------------------------------")
docs = datastore_client.get(datastore_client.key("users", "Bosch"))
print(docs)


print("-----------------------------------------------------")
docs = datastore_client.get(datastore_client.key("users", "Bach"))
print(docs)

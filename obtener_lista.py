from sharepoint import obtener_token
import requests
import json

SITE_ID = "ltdavivaseguros.sharepoint.com,d19e975d-3de3-41ae-8e04-f8b3cb41d412,9de98400-fdc6-40d6-ba92-cb96c8091105"

token = obtener_token()

headers = {
    "Authorization": f"Bearer {token}"
}

url = f"https://graph.microsoft.com/v1.0/sites/{SITE_ID}/lists"

r = requests.get(url, headers=headers)

print("STATUS:", r.status_code)

datos = r.json()

for lista in datos["value"]:
    print("LISTA:", lista["displayName"])
    print("ID:", lista["id"])
    print("------------------------")
from sharepoint import obtener_token
import requests

token = obtener_token()

headers = {
    "Authorization": f"Bearer {token}"
}

url = "https://graph.microsoft.com/v1.0/sites/ltdavivaseguros.sharepoint.com:/sites/CRMVivaAP"

r = requests.get(url, headers=headers)

print("STATUS:", r.status_code)

if r.status_code == 200:
    datos = r.json()
    print("SITE_ID:")
    print(datos["id"])
else:
    print(r.text)
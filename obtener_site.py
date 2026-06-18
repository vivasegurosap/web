import requests
from sharepoint import obtener_token

token = obtener_token()

headers = {
    "Authorization": f"Bearer {token}"
}

url = "https://graph.microsoft.com/v1.0/sites/ltdavivaseguros.sharepoint.com:/sites/CRMVivaAP"

resp = requests.get(url, headers=headers)

print("STATUS:", resp.status_code)
print(resp.text)
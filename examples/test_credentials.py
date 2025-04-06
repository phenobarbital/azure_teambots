import requests
from azure_teambots.conf import (
    MS_TENANT_ID,
    MS_CLIENT_ID,
    MS_CLIENT_SECRET
)

domain = 'https://login.microsoftonline.com'
token_endpoint = f'{domain}/{MS_TENANT_ID}/oauth2/v2.0/token'
client_id = MS_CLIENT_ID
client_secret = MS_CLIENT_SECRET

print(' Client : ', token_endpoint)
token_data = {
    'grant_type': 'client_credentials',
    'client_id': client_id,
    'client_secret': client_secret,
    'scope': 'https://graph.microsoft.com/.default'
}

token_response = requests.post(token_endpoint, data=token_data)

if token_response.status_code == 200:
    print('Token acquired successfully')
else:
    print('Failed to get token:', token_response.text)

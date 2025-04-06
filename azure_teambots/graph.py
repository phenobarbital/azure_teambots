# New file: azure_teambots/graph/client.py
import aiohttp
import json
from typing import Dict, Any, Optional
from navconfig.logging import logging

class GraphClient:
    """Helper class for Microsoft Graph API interactions."""

    def __init__(self, client_id: str, client_secret: str, tenant_id: str):
        self.client_id = client_id
        self.client_secret = client_secret
        self.tenant_id = tenant_id
        self.access_token = None
        self.logger = logging.getLogger("AzureBot.GraphClient")

    async def get_access_token(self) -> str:
        """Get an access token for Microsoft Graph API."""
        if self.access_token:
            return self.access_token

        token_url = f"https://login.microsoftonline.com/{self.tenant_id}/oauth2/v2.0/token"
        payload = {
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "scope": "https://graph.microsoft.com/.default",
            "grant_type": "client_credentials"
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(token_url, data=payload) as response:
                    if response.status == 200:
                        result = await response.json()
                        self.access_token = result.get("access_token")
                        return self.access_token
                    else:
                        error_text = await response.text()
                        self.logger.error(f"Error getting access token: {error_text}")
                        return None
        except Exception as e:
            self.logger.error(f"Exception during token acquisition: {str(e)}")
            return None

    async def get_user_by_upn(self, upn: str) -> Optional[Dict[str, Any]]:
        """Get user information from Graph API by UPN."""
        token = await self.get_access_token()
        if not token:
            return None

        url = f"https://graph.microsoft.com/v1.0/users/{upn}"
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers) as response:
                    if response.status == 200:
                        return await response.json()
                    else:
                        error_text = await response.text()
                        self.logger.error(f"Error fetching user {upn}: {error_text}")
                        return None
        except Exception as e:
            self.logger.error(f"Exception during Graph API call: {str(e)}")
            return None

    async def get_user_manager(self, upn: str) -> Optional[Dict[str, Any]]:
        """Get user's manager information."""
        token = await self.get_access_token()
        if not token:
            return None

        url = f"https://graph.microsoft.com/v1.0/users/{upn}/manager"
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers) as response:
                    if response.status == 200:
                        return await response.json()
                    else:
                        error_text = await response.text()
                        self.logger.error(f"Error fetching manager for {upn}: {error_text}")
                        return None
        except Exception as e:
            self.logger.error(f"Exception during Graph API call: {str(e)}")
            return None

    async def get_user_photo(self, upn: str) -> Optional[bytes]:
        """Get user's profile photo."""
        token = await self.get_access_token()
        if not token:
            return None

        url = f"https://graph.microsoft.com/v1.0/users/{upn}/photo/$value"
        headers = {
            "Authorization": f"Bearer {token}"
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers) as response:
                    if response.status == 200:
                        return await response.read()
                    else:
                        self.logger.warning(f"No photo found for user {upn} (Status: {response.status})")
                        return None
        except Exception as e:
            self.logger.error(f"Exception during Graph API call: {str(e)}")
            return None

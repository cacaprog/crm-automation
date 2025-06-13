# core/crm_client.py

import os
import requests
import json
import logging
from models.lead import Lead

logger = logging.getLogger(__name__)

class CrmApiClient:
    """Handles sending leads to a generic CRM API."""

    def __init__(self):
        # Generic configuration loaded from environment variables.
        self.api_url = os.getenv("CRM_API_URL")
        self.api_token = os.getenv("CRM_API_TOKEN_SECRET")

        if not self.api_url:
            raise ValueError("Environment variable CRM_API_URL is missing.")
        if not self.api_token:
            raise ValueError("Could not load CRM API token. Ensure CRM_API_TOKEN_SECRET is configured correctly in the environment.")

    def send_lead(self, lead: Lead, team_name: str) -> bool:
        """
        Formats and sends a single lead to the CRM API.
        """
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "Authorization": f"Bearer {self.api_token}"
        }

        # Constructing a generic "body" field for additional lead details.
        body_parts = []
        if lead.unit:
            body_parts.append(f"Unit of Interest: {lead.unit}")
        if lead.question1:
            body_parts.append(f"Question 1: {lead.question1}")
        if lead.question2:
            body_parts.append(f"Question 2: {lead.question2}")
        if lead.notes:
            body_parts.append(f"\nOriginal Notes: {lead.notes}")
        
        body_content = "\n".join(body_parts)

        # --- CRITICAL FOR ADAPTATION ---
        # The payload structure below is an example and MUST be adapted
        # to the specific requirements of the target CRM's API.
        # This example uses a common `data -> attributes` structure.
        lead_data_attributes = {
            "name": lead.name,
            "email": lead.email,
            "phone": lead.phone,
            "source": f"Lead Manager - {lead.source}",
            "description": f"[{team_name}] - New lead registered",
            "body": body_content
        }

        payload = {"data": {"attributes": lead_data_attributes}}

        try:
            response = requests.post(self.api_url, headers=headers, json=payload)
            response.raise_for_status()
            logger.info(f"Successfully sent lead '{lead.name}' to CRM for team '{team_name}'.")
            return True
        except requests.exceptions.HTTPError as err:
            logger.error(f"HTTP Error sending lead '{lead.name}': {err}")
            logger.error(f"Response Status: {err.response.status_code}")
            logger.error(f"Response Body: {err.response.text}")
        except requests.exceptions.RequestException as e:
            logger.error(f"An error occurred sending lead '{lead.name}': {e}")
        
        return False

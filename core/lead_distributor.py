# core/lead_distributor.py

import os
import math
import random
import logging
from typing import List
from datetime import datetime
from models.lead import Lead
from core.sheet_manager import GoogleSheetsManager
from core.crm_client import CrmApiClient # Updated import

logger = logging.getLogger(__name__)

class LeadDistributor:
    def __init__(self):
        # --- CONFIGURATION ---
        # Team names and distribution ratio are loaded from environment variables.
        # Default values are provided for easy setup.
        self.team_a_name = os.getenv("TEAM_A_NAME", "Team A")
        self.team_b_name = os.getenv("TEAM_B_NAME", "Team B")
        self.split_ratio = float(os.getenv("DISTRIBUTION_PERCENTAGE_A", 0.5)) # Default to 50/50 split

        if not 0.0 <= self.split_ratio <= 1.0:
            raise ValueError("DISTRIBUTION_PERCENTAGE_A must be between 0.0 and 1.0.")

        self.sheets = GoogleSheetsManager()
        self.api_client = CrmApiClient() # Use the renamed, generic client

    def distribute_leads(self) -> bool:
        """Fetches new leads from the sheet and distributes them via the CRM API."""
        logger.info("Checking for new leads to distribute...")
        
        leads = self.sheets.get_new_leads()
        if not leads:
            logger.info("No new leads in the sheet to distribute.")
            return False

        logger.info(f"Found {len(leads)} new leads. Starting distribution...")
        random.shuffle(leads) # Shuffle to ensure random distribution
        
        split_index = math.ceil(len(leads) * self.split_ratio)
        team_a_leads = leads[:split_index]
        team_b_leads = leads[split_index:]

        # Assign and send leads to each team
        sent_a_count = self._assign_and_send_leads(team_a_leads, self.team_a_name)
        sent_b_count = self._assign_and_send_leads(team_b_leads, self.team_b_name)

        logger.info(f"Distribution complete: {sent_a_count} sent to {self.team_a_name}, {sent_b_count} sent to {self.team_b_name}.")
        return True

    def _assign_and_send_leads(self, leads: List[Lead], team_name: str) -> int:
        """
        Sends a list of leads to the API and updates their status on the sheet.
        Returns the number of leads successfully sent.
        """
        if not leads:
            return 0
        
        logger.info(f"Processing {len(leads)} leads for {team_name}.")
        successful_sends = 0
        
        for lead in leads:
            success = self.api_client.send_lead(lead, team_name)
            
            if success:
                # Update status on the spreadsheet for tracking
                lead.status = f"Sent to {team_name} via API"
                self.sheets.update_lead_status(lead)
                successful_sends += 1
            else:
                logger.warning(f"Failed to send lead {lead.name} for {team_name}. It will be retried on the next run.")
                
        return successful_sends

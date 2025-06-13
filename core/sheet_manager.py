# core/sheet_manager.py

import gspread
import logging
import google.auth
import re
from typing import List, Dict
from datetime import datetime
from models.lead import Lead
import os

logger = logging.getLogger(__name__)

class GoogleSheetsManager:
    def __init__(self):
        self.spreadsheet_id = os.getenv("SPREADSHEET_ID")
        # Use generic names for sheet tabs, configured via environment variables.
        self.primary_sheet_name = os.getenv("PRIMARY_SHEET_NAME", "leads")
        self.ads_sheet_name = os.getenv("ADS_SHEET_NAME", "meta_leads")

        if not self.spreadsheet_id:
            raise ValueError("Environment variable SPREADSHEET_ID is missing.")

        try:
            # Use default application credentials for secure authentication on GCP.
            creds, _ = google.auth.default(scopes=['https://www.googleapis.com/auth/spreadsheets'])
            self.client = gspread.authorize(creds)
            
            spreadsheet = self.client.open_by_key(self.spreadsheet_id)
            self.primary_sheet = spreadsheet.worksheet(self.primary_sheet_name)
            self.meta_sheet = spreadsheet.worksheet(self.ads_sheet_name)
            
            # Create a map of header names to column indexes for robustness.
            self._primary_header_map = self._get_header_map(self.primary_sheet)
            self._meta_header_map = self._get_header_map(self.meta_sheet)
            logger.info("Google Sheets Manager initialized successfully.")
        except Exception as e:
            logger.error(f"Failed to initialize GoogleSheetsManager: {e}")
            raise

    def _get_header_map(self, sheet: gspread.Worksheet) -> Dict[str, int]:
        """Creates a mapping of header names to their column index (1-based)."""
        try:
            header = sheet.row_values(1)
            return {name.strip(): i + 1 for i, name in enumerate(header)}
        except Exception as e:
            logger.error(f"Could not read header row from sheet '{sheet.title}': {e}")
            return {}

    def get_new_leads(self) -> List[Lead]:
        """
        Retrieves all new leads from all configured sources (sheets)
        and returns them as a single consolidated list.
        """
        all_new_leads = []
        
        # --- NOTE: Column names used here ('Status', 'Name', etc.) must match ---
        # --- your headers in the Google Sheet for the script to work correctly. ---
        try:
            all_rows = self.primary_sheet.get_all_records() # Reads data as dicts
            for i, lead_data in enumerate(all_rows, start=2):
                if lead_data.get("Status", "").lower().strip() == "new":
                    all_new_leads.append(Lead(
                        name=lead_data.get("Name"), email=lead_data.get("Email"),
                        phone=lead_data.get("Phone"), unit=lead_data.get("Unit"),
                        source=lead_data.get("Source", "email_import"), notes=lead_data.get("Notes"),
                        row_number=i, is_facebook_lead=False
                    ))
        except Exception as e:
            logger.error(f"Error fetching leads from primary sheet '{self.primary_sheet_name}': {e}")
            
        # Fetch leads from the secondary (e.g., ads) sheet.
        ads_leads = self._get_ads_leads()
        all_new_leads.extend(ads_leads)
        
        if all_new_leads:
            logger.info(f"Fetched a total of {len(all_new_leads)} new leads from all sources.")
        
        return all_new_leads

    def _get_ads_leads(self) -> List[Lead]:
        """Fetches new leads from the ads sheet (e.g., from Meta/Facebook)."""
        fb_leads = []
        try:
            all_rows = self.meta_sheet.get_all_records()
            for i, lead_data in enumerate(all_rows, start=2):
                # Process rows that have an empty status.
                if not lead_data.get("Status", "").strip():
                    phone_val = str(lead_data.get("Phone", ""))
                    # --- Example of data normalization ---
                    if phone_val:
                        cleaned_phone = re.sub(r'\D', '', phone_val)
                        # Example: Strip '55' country code if present at the beginning of a long number.
                        if cleaned_phone.startswith('55') and len(cleaned_phone) > 11:
                            phone_val = cleaned_phone[2:]
                        else:
                            phone_val = cleaned_phone

                    q1_val = lead_data.get("Question 1", "")
                    
                    fb_leads.append(Lead(
                        name=lead_data.get("Full Name", "Unknown"),
                        email=lead_data.get("Email", ""),
                        phone=phone_val,
                        unit=q1_val, # Use a custom question as the 'unit'.
                        source="ads_import",
                        row_number=i,
                        is_facebook_lead=True,
                        question1=q1_val,
                        question2=lead_data.get("Question 2", "")
                    ))
            if fb_leads: logger.info(f"Found {len(fb_leads)} new leads from ads sheet.")
            return fb_leads
        except Exception as e:
            logger.error(f"Error fetching leads from ads sheet: {e}")
            return []

    def update_lead_status(self, lead: Lead) -> bool:
        """Updates the status of a lead in the correct sheet."""
        if lead.row_number is None: return False

        try:
            sheet_to_update = self.meta_sheet if lead.is_facebook_lead else self.primary_sheet
            header_map = self._meta_header_map if lead.is_facebook_lead else self._primary_header_map
            status_col = header_map.get("Status")
            
            if not status_col: 
                logger.error(f"Could not find 'Status' column in sheet '{sheet_to_update.title}'.")
                return False

            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            new_status_value = f"{lead.status} ({timestamp})"
            sheet_to_update.update_cell(lead.row_number, status_col, new_status_value)
            
            logger.info(f"Updated lead in row {lead.row_number} of sheet '{sheet_to_update.title}' to status '{lead.status}'")
            return True
        except Exception as e:
            logger.error(f"Failed to update status for lead in row {lead.row_number}: {e}")
            return False

    def add_lead(self, lead: Lead) -> bool:
        """Adds a new lead (e.g., from email) to the primary sheet."""
        try:
            # The order here must match the column order in the primary sheet.
            row_data = [
                datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                lead.name, lead.email, lead.phone, lead.unit,
                lead.source, lead.notes, "new", "", "" # Status, and empty placeholder columns
            ]
            self.primary_sheet.append_row(row_data)
            logger.info(f"Successfully added lead to sheet '{self.primary_sheet_name}': {lead.summary()}")
            return True
        except Exception as e:
            logger.error(f"Failed to add lead to sheet '{self.primary_sheet_name}': {e}")
            return False

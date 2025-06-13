# models/lead.py

from dataclasses import dataclass
from typing import Optional

@dataclass
class Lead:
    """
    Data class representing a lead with full tracking and origin info.
    This structure is used to pass lead data between different modules of the system.
    """
    # Core lead information
    name: str
    email: str
    phone: str
    unit: str

    # --- NOVO ---
    # Custom fields for additional information from lead forms.
    # Can be adapted or extended as needed.
    question1: Optional[str] = None
    question2: Optional[str] = None

    # Metadata for tracking and processing
    source: str = "email_import"
    notes: str = ""
    status: str = "new"

    # Internal tracking properties
    row_number: Optional[int] = None
    is_facebook_lead: bool = False # Flag to identify the lead's origin sheet
    
    # Distribution tracking
    distributed_to: Optional[str] = None
    distribution_time: Optional[str] = None

    def summary(self) -> str:
        """Generates a short, log-friendly summary of the lead."""
        return f"Lead(Name: {self.name}, Phone: {self.phone}, Source: {self.source})"

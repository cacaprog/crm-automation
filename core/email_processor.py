# core/email_processor.py

import imaplib
import email
import re
import os
import logging
from email.header import decode_header
from email.message import Message
from typing import List, Dict, Optional
from models.lead import Lead

logger = logging.getLogger(__name__)

class EmailProcessor:
    """Handles connecting to an email server and parsing leads from emails."""

    def __init__(self):
        # Configuration loaded from environment variables.
        self.imap_host = os.getenv("IMAP_HOST")
        self.imap_port = int(os.getenv("IMAP_PORT", 993)) # Default SSL port
        self.imap_user = os.getenv("IMAP_USER")
        self.imap_password = os.getenv("IMAP_PASSWORD_SECRET")

        if not all([self.imap_host, self.imap_user, self.imap_password]):
            raise ValueError("IMAP environment variables (HOST, USER, PASSWORD_SECRET) are not fully configured.")

    def connect(self) -> imaplib.IMAP4_SSL:
        """Establishes and returns a connection to the IMAP server."""
        try:
            mail = imaplib.IMAP4_SSL(self.imap_host, self.imap_port)
            mail.login(self.imap_user, self.imap_password)
            mail.select("inbox")
            return mail
        except Exception as e:
            logger.error(f"Failed to connect to IMAP server: {e}")
            raise

    def process_unread_emails(self) -> List[Lead]:
        """Fetches all unread emails, processes them, and returns them as a list of Leads."""
        leads = []
        mail = None
        try:
            mail = self.connect()
            status, messages = mail.search(None, '(UNSEEN)')
            if status != "OK":
                logger.error("Failed to search for unread emails.")
                return []
            
            email_ids = messages[0].split()
            if email_ids:
                logger.info(f"Found {len(email_ids)} unread email(s).")
            
            for eid in email_ids:
                try:
                    lead = self._process_single_email(mail, eid)
                    if lead:
                        leads.append(lead)
                        mail.store(eid, '+FLAGS', '\\Seen') # Mark email as read
                except Exception as e:
                    logger.warning(f"Could not process email with ID {eid}: {e}")
        finally:
            if mail:
                try:
                    mail.close()
                    mail.logout()
                except Exception as e:
                    logger.warning(f"Error during IMAP logout: {e}")
        return leads

    def _process_single_email(self, mail: imaplib.IMAP4_SSL, mail_id: bytes) -> Optional[Lead]:
        """Fetches and parses a single email into a Lead object."""
        status, data = mail.fetch(mail_id, '(RFC822)')
        if status != "OK": return None

        raw_email = data[0][1]
        msg = email.message_from_bytes(raw_email)
        subject = self._decode_header(msg.get("Subject", "No Subject"))
        body = self._get_body(msg)
        if not body: return None

        parsed_data = self._parse_body(body)
        if not any([parsed_data.get("email"), parsed_data.get("phone")]):
            return None # Skip if no contact info is found

        return Lead(
            name=parsed_data.get("name", "Unknown"),
            email=parsed_data.get("email"),
            phone=parsed_data.get("phone"),
            unit=parsed_data.get("unit"),
            notes=f"Imported from email. Subject: {subject}"
        )

    @staticmethod
    def _decode_header(header: str) -> str:
        parts = decode_header(header)
        return ''.join(p[0].decode(p[1] or 'utf-8', errors='ignore') if isinstance(p[0], bytes) else p[0] for p in parts)

    @staticmethod
    def _get_body(msg: Message) -> str:
        if msg.is_multipart():
            for part in msg.walk():
                if part.get_content_type() == "text/plain" and "attachment" not in str(part.get("Content-Disposition")):
                    try:
                        return part.get_payload(decode=True).decode(part.get_content_charset() or 'utf-8', errors='ignore')
                    except Exception:
                        continue
        else:
            try:
                return msg.get_payload(decode=True).decode(msg.get_content_charset() or 'utf-8', errors='ignore')
            except Exception:
                return ""
        return ""

    @staticmethod
    def _parse_body(body: str) -> Dict[str, Optional[str]]:
        """
        Parses the email body using regex to find lead information.
        This method is the primary place for customization based on email template formats.
        """
        data = {}
        # --- CUSTOMIZATION POINT ---
        # These regex patterns should be adapted to match the format of your lead emails.
        patterns = {
            "name": r"(?:Name|Nome):\s*(.*?)(?:\n|$)",
            "email": r"Email:\s*([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})",
            "phone": r"(?:Phone|Telefone|Whatsapp):\s*([\+\d\s\(\)\-.]+?)(?:\n|$)",
            "unit": r"(?:Unit|Unidade):\s*(.*?)(?:\n|$)",
        }
        for key, pattern in patterns.items():
            match = re.search(pattern, body, re.IGNORECASE | re.DOTALL)
            if match:
                value = match.group(1).strip()
                # Clean phone number by removing non-digit characters (except '+')
                data[key] = re.sub(r'[^\d\+]', '', value) if key == "phone" else value
        return data

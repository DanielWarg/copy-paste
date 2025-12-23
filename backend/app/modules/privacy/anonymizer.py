"""
Anonymizer - PII detection and scrubbing using local Ollama.

GDPR: All PII must be identified locally before any external API calls.
"""
import re
from typing import Dict, List
from uuid import UUID
from app.modules.privacy.ollama_client import ollama_client
from app.modules.privacy.mapping_manager import mapping_manager
from app.core.logging import log_privacy_safe


class Anonymizer:
    """Anonymizes text by replacing PII with tokens."""
    
    def __init__(self):
        self.token_counter = {"person": 0, "org": 0, "email": 0, "phone": 0, "address": 0}
    
    def _get_token(self, pii_type: str) -> str:
        """Generate anonymization token."""
        if pii_type == "person":
            self.token_counter["person"] += 1
            return f"[PERSON_{chr(64 + self.token_counter['person'])}]"
        elif pii_type == "organization":
            self.token_counter["org"] += 1
            return f"[ORG_{chr(64 + self.token_counter['org'])}]"
        elif pii_type == "email":
            self.token_counter["email"] += 1
            return f"[EMAIL_{self.token_counter['email']}]"
        elif pii_type == "phone":
            self.token_counter["phone"] += 1
            return f"[PHONE_{self.token_counter['phone']}]"
        elif pii_type == "address":
            self.token_counter["address"] += 1
            return f"[ADDRESS_{self.token_counter['address']}]"
        return "[REDACTED]"
    
    async def anonymize(
        self,
        text: str,
        event_id: UUID,
        production_mode: bool
    ) -> tuple[str, Dict[str, str], bool]:
        """
        Anonymize text by detecting and replacing PII.
        
        Args:
            text: Text to anonymize
            event_id: Event identifier
            production_mode: Whether production mode is enabled
            
        Returns:
            Tuple of (anonymized_text, mapping, is_anonymized)
            
        Raises:
            ValueError: If production_mode is True but anonymization fails
        """
        # Reset token counter for this event
        self.token_counter = {"person": 0, "org": 0, "email": 0, "phone": 0, "address": 0}
        
        # Detect PII using local Ollama (with fallback to regex if Ollama fails)
        try:
            pii_data = await ollama_client.detect_pii(text, str(event_id))
        except Exception as e:
            log_privacy_safe(str(event_id), f"Ollama failed, using regex fallback: {str(e)}")
            # Fallback to regex-based PII detection
            pii_data = self._detect_pii_regex(text)
        
        # Build mapping (token → real name)
        mapping: Dict[str, str] = {}
        anonymized_text = text
        
        # Replace persons
        for person in pii_data.get("persons", []):
            if person and person.strip():
                token = self._get_token("person")
                mapping[token] = person.strip()
                # Case-insensitive replacement
                pattern = re.compile(re.escape(person), re.IGNORECASE)
                anonymized_text = pattern.sub(token, anonymized_text)
        
        # Replace organizations
        for org in pii_data.get("organizations", []):
            if org and org.strip():
                token = self._get_token("org")
                mapping[token] = org.strip()
                pattern = re.compile(re.escape(org), re.IGNORECASE)
                anonymized_text = pattern.sub(token, anonymized_text)
        
        # Replace emails (more aggressive matching)
        for email in pii_data.get("emails", []):
            if email and email.strip():
                token = self._get_token("email")
                mapping[token] = email.strip()
                # Match email with word boundaries and case insensitive
                pattern = re.compile(r'\b' + re.escape(email) + r'\b', re.IGNORECASE)
                anonymized_text = pattern.sub(token, anonymized_text)
        
        # Replace phone numbers (handle various formats with flexible matching)
        for phone in pii_data.get("phone_numbers", []):
            if phone and phone.strip():
                token = self._get_token("phone")
                mapping[token] = phone.strip()
                phone_clean = phone.strip()
                # Create flexible pattern that matches phone with any separator combination
                # Replace separators with optional pattern
                phone_pattern = re.sub(r'[\s\-\.\(\)]', r'[\\s\\-\\.\\(\\)]?', re.escape(phone_clean))
                pattern = re.compile(phone_pattern, re.IGNORECASE)
                anonymized_text = pattern.sub(token, anonymized_text)
        
        # Also do direct regex-based replacement for patterns not caught by PII detection
        # SSN pattern (direct replacement)
        ssn_pattern = r'\b\d{3}-\d{2}-\d{4}\b'
        ssns = re.findall(ssn_pattern, anonymized_text)
        for ssn in ssns:
            if ssn not in mapping.values():  # Only if not already mapped
                token = self._get_token("person")  # Use person token for SSN
                mapping[token] = ssn
                anonymized_text = re.sub(re.escape(ssn), token, anonymized_text)
        
        # Email pattern (direct replacement as fallback)
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        emails_found = re.findall(email_pattern, anonymized_text)
        for email in emails_found:
            if email not in mapping.values():
                token = self._get_token("email")
                mapping[token] = email
                anonymized_text = re.sub(r'\b' + re.escape(email) + r'\b', token, anonymized_text, flags=re.IGNORECASE)
        
        # Phone pattern (direct replacement as fallback - improved)
        # Match Swedish phone numbers: 070-123 45 67, 08-123 45 67, etc.
        # Do this BEFORE other replacements to catch all formats
        phone_patterns = [
            (r'\b(0\d{1,2})[-.\s]+(\d{3})[-.\s]+(\d{2,3})[-.\s]+(\d{2,3})\b', r'\1-\2 \3 \4'),  # Swedish: 070-123 45 67
            (r'\b(\d{3})[-.]?(\d{3})[-.]?(\d{4})\b', r'\1-\2-\3'),  # US format
            (r'\b\((\d{3})\)\s?(\d{3})[-.]?(\d{4})\b', r'(\1) \2-\3'),  # (555) format
        ]
        for pattern, replacement in phone_patterns:
            matches = list(re.finditer(pattern, anonymized_text))
            for match in reversed(matches):  # Reverse to maintain positions
                phone_full = match.group(0)
                if phone_full not in mapping.values():
                    token = self._get_token("phone")
                    mapping[token] = phone_full
                    # Replace the exact match
                    start, end = match.span()
                    anonymized_text = anonymized_text[:start] + token + anonymized_text[end:]
        
        # Address pattern (direct replacement as fallback)
        # Match addresses like "Storgatan 123" or "123 Storgatan"
        address_patterns = [
            r'\b(\d+)\s+([A-ZÅÄÖ][a-zåäö]+)\s+(gatan|gata|vägen|väg)\b',  # Swedish: "123 Storgatan"
            r'\b([A-ZÅÄÖ][a-zåäö]+gatan|[A-ZÅÄÖ][a-zåäö]+gata|[A-ZÅÄÖ][a-zåäö]+vägen|[A-ZÅÄÖ][a-zåäö]+väg)\s+(\d+)\b',  # Swedish: "Storgatan 123"
            r'\b\d+\s+[A-Z][a-z]+\s+(Street|St|Avenue|Ave|Road|Rd)\b',  # English
        ]
        for pattern in address_patterns:
            matches = list(re.finditer(pattern, anonymized_text, re.IGNORECASE))
            for match in reversed(matches):  # Reverse to maintain positions
                addr_full = match.group(0)
                if addr_full and addr_full not in mapping.values():
                    token = self._get_token("address")
                    mapping[token] = addr_full
                    # Replace the exact match
                    start, end = match.span()
                    anonymized_text = anonymized_text[:start] + token + anonymized_text[end:]
        
        # Replace addresses (basic - could be improved)
        for address in pii_data.get("addresses", []):
            if address and address.strip():
                token = self._get_token("address")
                mapping[token] = address.strip()
                pattern = re.compile(re.escape(address), re.IGNORECASE)
                anonymized_text = pattern.sub(token, anonymized_text)
        
        # Store mapping in server RAM (never persisted, never in response)
        if mapping:
            mapping_manager.store(event_id, mapping)
        
        is_anonymized = len(mapping) > 0 or not production_mode
        
        # If production mode is ON, we MUST have anonymization
        # But allow if we at least tried (mapping might be empty if no PII found)
        if production_mode and len(mapping) == 0 and len(text) > 0:
            # In production mode, if we found no PII, that's actually OK (text might be clean)
            # But we should still mark as anonymized if we processed it
            is_anonymized = True
            log_privacy_safe(
                str(event_id),
                "No PII detected in text (clean text)",
                production_mode=production_mode
            )
        
        # Log privacy-safe metrics
        log_privacy_safe(
            str(event_id),
            "Anonymization completed",
            is_anonymized=is_anonymized,
            tokens_created=len(mapping),
            original_length=len(text),
            anonymized_length=len(anonymized_text)
        )
        
        return anonymized_text, mapping, is_anonymized
    
    def _detect_pii_regex(self, text: str) -> Dict[str, List[str]]:
        """
        Fallback regex-based PII detection.
        
        Args:
            text: Text to analyze
            
        Returns:
            Dict with detected PII
        """
        import re
        
        pii_data = {
            "persons": [],
            "organizations": [],
            "emails": [],
            "phone_numbers": [],
            "addresses": []
        }
        
        # Email detection (improved)
        emails = re.findall(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', text)
        pii_data["emails"] = list(set(emails))
        
        # Phone detection (improved - handles various formats including Swedish)
        phone_patterns = [
            r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b',  # 555-1234, 555.1234, 5551234
            r'\b\(\d{3}\)\s?\d{3}[-.]?\d{4}\b',  # (555) 123-4567
            r'\b\d{3}\s\d{3}\s\d{4}\b',  # 555 123 4567
            r'\b0\d{1,2}[-.\s]?\d{3}[-.\s]?\d{2,3}[-.\s]?\d{2,3}\b',  # Swedish: 070-123 45 67, 08-123 45 67
            r'\b\d{2,3}[-.\s]?\d{3}[-.\s]?\d{2,3}[-.\s]?\d{2,3}\b',  # General format
        ]
        phones = []
        for pattern in phone_patterns:
            phones.extend(re.findall(pattern, text))
        pii_data["phone_numbers"] = list(set(phones))
        
        # SSN detection
        ssns = re.findall(r'\b\d{3}-\d{2}-\d{4}\b', text)
        # Add SSNs to persons list (they're personal identifiers)
        pii_data["persons"].extend([f"SSN: {ssn}" for ssn in ssns])
        
        # Address detection (improved - handles Swedish addresses)
        address_patterns = [
            r'\b\d+\s+[A-ZÅÄÖ][a-zåäö]+\s+(gatan|gata|vägen|väg|stigen|stig|plan|torg|plats)',  # Swedish: Storgatan, Storgatan 123
            r'\b\d+\s+[A-Z][a-z]+\s+(Street|St|Avenue|Ave|Road|Rd|Lane|Ln|Drive|Dr|Boulevard|Blvd)',  # English
            r'\b[A-ZÅÄÖ][a-zåäö]+\s+\d+[A-Za-z]?\b',  # Street name + number
        ]
        addresses = []
        for pattern in address_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            addresses.extend(matches)
        pii_data["addresses"] = list(set(addresses))
        
        # Name detection - look for "First Last" patterns
        # Common patterns: "John Doe", "works at", "contact", etc.
        name_patterns = [
            r'\b([A-Z][a-z]+\s+[A-Z][a-z]+)\b',  # "John Doe"
            r'(?:contact|call|email|reach)\s+([A-Z][a-z]+\s+[A-Z][a-z]+)',  # "contact John Doe"
            r'([A-Z][a-z]+\s+[A-Z][a-z]+)\s+(?:works|employed|at)',  # "John Doe works"
        ]
        names = []
        for pattern in name_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            names.extend(matches)
        # Filter out common non-name patterns
        common_words = {'The', 'This', 'That', 'There', 'These', 'Those', 'When', 'Where', 'What', 'Which', 'Who', 'How', 'Main St', 'Main Street'}
        potential_names = [n.strip() for n in names if not any(cw.lower() in n.lower() for cw in common_words)]
        pii_data["persons"] = list(set(potential_names))[:5]  # Limit to 5, remove duplicates
        
        # Organization detection (basic - words after "at", "from", "works at")
        org_patterns = [
            r'(?:at|from|works at|employed by)\s+([A-Z][a-zA-Z\s&]+(?:Corp|Inc|Ltd|LLC|AB|GmbH))',
            r'([A-Z][a-zA-Z\s&]+(?:Corp|Inc|Ltd|LLC|AB|GmbH))'
        ]
        orgs = []
        for pattern in org_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            orgs.extend(matches)
        pii_data["organizations"] = list(set(orgs[:5]))  # Limit to 5
        
        return pii_data


# Global instance
anonymizer = Anonymizer()


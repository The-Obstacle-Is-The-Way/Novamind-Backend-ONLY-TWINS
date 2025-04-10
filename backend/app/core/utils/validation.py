# -*- coding: utf-8 -*-
"""
Validation utilities for Novamind Digital Twin Platform.

This module contains validation functions for various data types,
including personal identifiable information (PII) and protected health
information (PHI) detection.
"""

import re
from typing import Any, Dict, List, Optional, Pattern, Set, Tuple, NamedTuple
import logging

logger = logging.getLogger(__name__)


class PHIMatch(NamedTuple):
    """Represents a match of PHI in text."""
    phi_type: str
    value: str
    start: int
    end: int


class PHIDetector:
    """
    Utility class for detecting PHI in strings.
    
    This class provides methods to scan text for potential protected health
    information to ensure HIPAA compliance.
    """
    
    # Regex patterns for detecting common PHI
    SSN_PATTERN = re.compile(r"\b\d{3}[-]?\d{2}[-]?\d{4}\b")
    EMAIL_PATTERN = re.compile(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}")
    PHONE_PATTERN = re.compile(r"\b(?:\+?1[-.]?)?(?:\(?([0-9]{3})\)?[-.]?)?([0-9]{3})[-.]?([0-9]{4})\b")
    DATE_PATTERN = re.compile(r"\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b|\b\d{4}[/-]\d{1,2}[/-]\d{1,2}\b")
    NAME_PATTERN = re.compile(r"\b[A-Z][a-z]+\s+[A-Z][a-z]+\b")
    MRN_PATTERN = re.compile(r"\bMRN\d+\b")
    ADDRESS_PATTERN = re.compile(r"\b\d+\s+[A-Za-z\s]+(?:St|Ave|Rd|Blvd|Dr|Lane|Ln|Way|Pl|Plaza|Court|Ct)\b", re.IGNORECASE)
    
    # Lists of common first and last names to check against
    COMMON_FIRST_NAMES = {
        "john", "james", "robert", "michael", "william", "david", "richard", "joseph", "thomas", "charles",
        "mary", "patricia", "jennifer", "linda", "elizabeth", "barbara", "susan", "jessica", "sarah", "karen"
    }
    
    COMMON_LAST_NAMES = {
        "smith", "johnson", "williams", "jones", "brown", "davis", "miller", "wilson", "moore", "taylor",
        "anderson", "thomas", "jackson", "white", "harris", "martin", "thompson", "garcia", "martinez", "robinson"
    }
    
    def __init__(self):
        """Initialize the PHI detector."""
        logger.debug("Initializing PHI detector")
    
    def contains_phi(self, text: str) -> bool:
        """
        Check if the provided text contains any PHI.
        
        Args:
            text: The text to check for PHI
            
        Returns:
            True if PHI is detected, False otherwise
        """
        if not text or not isinstance(text, str):
            return False
            
        # Check for patterns
        if (self.SSN_PATTERN.search(text) or
            self.EMAIL_PATTERN.search(text) or
            self.PHONE_PATTERN.search(text) or
            self.DATE_PATTERN.search(text) or
            self.MRN_PATTERN.search(text) or
            self.ADDRESS_PATTERN.search(text)):
            return True
            
        # Check for names
        for name_match in self.NAME_PATTERN.finditer(text):
            name = name_match.group(0).lower()
            first_last = name.split()
            if len(first_last) >= 2:
                first, last = first_last[0], first_last[-1]
                if first in self.COMMON_FIRST_NAMES or last in self.COMMON_LAST_NAMES:
                    return True
        
        return False
    
    def detect_phi(self, text: str) -> List[PHIMatch]:
        """
        Detect all instances of PHI in the provided text.
        
        Args:
            text: The text to scan for PHI
            
        Returns:
            List of PHIMatch tuples containing PHI type, value, start position, and end position
        """
        if not text or not isinstance(text, str):
            return []
            
        matches = []
        
        # Check for SSNs
        for match in self.SSN_PATTERN.finditer(text):
            matches.append(PHIMatch(
                phi_type="SSN",
                value=match.group(0),
                start=match.start(),
                end=match.end()
            ))
        
        # Check for email addresses
        for match in self.EMAIL_PATTERN.finditer(text):
            matches.append(PHIMatch(
                phi_type="EMAIL",
                value=match.group(0),
                start=match.start(),
                end=match.end()
            ))
        
        # Check for phone numbers
        for match in self.PHONE_PATTERN.finditer(text):
            matches.append(PHIMatch(
                phi_type="PHONE",
                value=match.group(0),
                start=match.start(),
                end=match.end()
            ))
        
        # Check for dates
        for match in self.DATE_PATTERN.finditer(text):
            matches.append(PHIMatch(
                phi_type="DOB",
                value=match.group(0),
                start=match.start(),
                end=match.end()
            ))
        
        # Check for medical record numbers
        for match in self.MRN_PATTERN.finditer(text):
            matches.append(PHIMatch(
                phi_type="MEDICAL_RECORD",
                value=match.group(0),
                start=match.start(),
                end=match.end()
            ))
        
        # Check for addresses
        for match in self.ADDRESS_PATTERN.finditer(text):
            matches.append(PHIMatch(
                phi_type="ADDRESS",
                value=match.group(0),
                start=match.start(),
                end=match.end()
            ))
        
        # Check for names
        for match in self.NAME_PATTERN.finditer(text):
            name = match.group(0)
            first_last = name.lower().split()
            if len(first_last) >= 2:
                first, last = first_last[0], first_last[-1]
                if first in self.COMMON_FIRST_NAMES or last in self.COMMON_LAST_NAMES:
                    matches.append(PHIMatch(
                        phi_type="NAME",
                        value=name,
                        start=match.start(),
                        end=match.end()
                    ))
        
        return matches


def validate_credit_card(cc_number: str) -> bool:
    """
    Validate a credit card number using the Luhn algorithm.
    
    Args:
        cc_number: The credit card number to validate
        
    Returns:
        True if the credit card number is valid, False otherwise
    """
    if not cc_number or not isinstance(cc_number, str):
        return False
        
    # Remove spaces and hyphens
    cc_number = cc_number.replace(" ", "").replace("-", "")
    
    # Check if all characters are digits
    if not cc_number.isdigit():
        return False
        
    # Check length (most cards are 13-19 digits)
    if not (13 <= len(cc_number) <= 19):
        return False
    
    # Luhn algorithm
    digits = [int(d) for d in cc_number]
    checksum = 0
    for i, digit in enumerate(reversed(digits)):
        if i % 2 == 1:  # Odd position (0-indexed from right)
            digit *= 2
            if digit > 9:
                digit -= 9
        checksum += digit
    
    return checksum % 10 == 0


def validate_email(email: str) -> bool:
    """
    Validate an email address.
    
    Args:
        email: The email address to validate
        
    Returns:
        True if the email address is valid, False otherwise
    """
    if not email or not isinstance(email, str):
        return False
        
    pattern = re.compile(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$")
    return bool(pattern.match(email))


def validate_phone_number(phone: str) -> bool:
    """
    Validate a phone number.
    
    Args:
        phone: The phone number to validate
        
    Returns:
        True if the phone number is valid, False otherwise
    """
    if not phone or not isinstance(phone, str):
        return False
        
    # Remove common non-digit characters
    clean_phone = re.sub(r"[().\-\s]", "", phone)
    
    # Check if it's a valid format
    if len(clean_phone) == 10 and clean_phone.isdigit():
        return True
    elif len(clean_phone) == 11 and clean_phone.startswith("1") and clean_phone.isdigit():
        return True
    else:
        return False


def validate_us_ssn(ssn: str) -> bool:
    """
    Validate a US Social Security Number.
    
    Args:
        ssn: The SSN to validate
        
    Returns:
        True if the SSN is valid, False otherwise
    """
    if not ssn or not isinstance(ssn, str):
        return False
        
    # Remove hyphens
    clean_ssn = ssn.replace("-", "")
    
    # Check if it's 9 digits
    if not (clean_ssn.isdigit() and len(clean_ssn) == 9):
        return False
    
    # Check for invalid patterns
    if clean_ssn.startswith("000") or clean_ssn.startswith("666"):
        return False
    if clean_ssn.startswith("9"):
        return False
    if clean_ssn[3:5] == "00":
        return False
    if clean_ssn[5:] == "0000":
        return False
    
    return True


def validate_date(date_str: str, format_str: str = "%Y-%m-%d") -> bool:
    """
    Validate a date string against a format.
    
    Args:
        date_str: The date string to validate
        format_str: The expected format of the date
        
    Returns:
        True if the date is valid, False otherwise
    """
    import datetime
    
    if not date_str or not isinstance(date_str, str):
        return False
        
    try:
        datetime.datetime.strptime(date_str, format_str)
        return True
    except ValueError:
        return False


def validate_ip_address(ip: str) -> bool:
    """
    Validate an IP address.
    
    Args:
        ip: The IP address to validate
        
    Returns:
        True if the IP address is valid, False otherwise
    """
    if not ip or not isinstance(ip, str):
        return False
        
    # IPv4 pattern
    ipv4_pattern = re.compile(
        r"^(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$"
    )
    
    # IPv6 pattern
    ipv6_pattern = re.compile(
        r"^(?:[0-9a-fA-F]{1,4}:){7}[0-9a-fA-F]{1,4}|"
        r"(?:[0-9a-fA-F]{1,4}:){1,7}:|"
        r"(?:[0-9a-fA-F]{1,4}:){1,6}:[0-9a-fA-F]{1,4}|"
        r"(?:[0-9a-fA-F]{1,4}:){1,5}(?::[0-9a-fA-F]{1,4}){1,2}|"
        r"(?:[0-9a-fA-F]{1,4}:){1,4}(?::[0-9a-fA-F]{1,4}){1,3}|"
        r"(?:[0-9a-fA-F]{1,4}:){1,3}(?::[0-9a-fA-F]{1,4}){1,4}|"
        r"(?:[0-9a-fA-F]{1,4}:){1,2}(?::[0-9a-fA-F]{1,4}){1,5}|"
        r"[0-9a-fA-F]{1,4}:(?:(?::[0-9a-fA-F]{1,4}){1,6})|"
        r":(?:(?::[0-9a-fA-F]{1,4}){1,7}|:)"
    )
    
    return bool(ipv4_pattern.match(ip) or ipv6_pattern.match(ip))

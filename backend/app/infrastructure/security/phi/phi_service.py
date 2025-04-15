# -*- coding: utf-8 -*-
"""
Centralized PHI Detection and Sanitization Service.

This module provides a unified service for handling Protected Health Information (PHI)
detection and sanitization across the application, ensuring HIPAA compliance.
It consolidates logic from various previous implementations.
"""

import re
import logging
from enum import Enum, auto
from typing import Any, Dict, List, Optional, Pattern, Set, Union, Tuple
from datetime import date, datetime, timezone # Added timezone
import uuid # For potential anonymous value generation

logger = logging.getLogger(__name__)

class PHIType(Enum):
    """Enumeration of PHI types for classification."""
    SSN = auto()
    ADDRESS = auto()
    EMAIL = auto()
    PHONE = auto()
    DOB = auto()
    NAME = auto()
    MRN = auto() # Medical Record Number / Patient ID
    POLICY_NUMBER = auto() # Insurance/Policy Numbers
    CREDIT_CARD = auto() # Credit Card Numbers
    AGE = auto() # Age over 89 (or potentially sensitive age mentions)
    DATE = auto() # General dates (potentially needing context)
    URL = auto() # URLs containing potential identifiers
    IP_ADDRESS = auto() # IP Addresses
    DEVICE_ID = auto() # Device Identifiers
    ACCOUNT_NUMBER = auto() # Financial Account Numbers
    LICENSE_NUMBER = auto() # Driver's license, professional license
    BIOMETRIC = auto() # Biometric identifiers (e.g., fingerprints - placeholder)
    PHOTO = auto() # Full face photographic images (placeholder)
    OTHER = auto() # Generic placeholder for less common types


class PHIService:
    """
    Unified service for PHI detection and sanitization.
    
    Combines regex patterns, context analysis, and sensitivity levels.
    """

    # --- Configuration ---
    # Sensitivity Levels:
    # low: Only explicit, high-confidence patterns (e.g., SSN format).
    # medium: Standard patterns, some context awareness (e.g., names after Dr.).
    # high: Aggressive matching, broader context checks, potential for more false positives.
    DEFAULT_SENSITIVITY = "medium"
    DEFAULT_REPLACEMENT_TEMPLATE = "[REDACTED {phi_type}]"

    # --- Core Pattern Definitions (Combined & Prioritized) ---
    # Priority: Higher number = matched first in overlaps. Type maps to PHIType enum.
    # Adapted from enhanced_phi_detector.py, phi_sanitizer.py, phi_sanitizer_from_utils.py
    _PATTERNS_DEFINITIONS: List[Dict[str, Any]] = [
        # High Priority Identifiers
        {
            "name": "SSN", "type": PHIType.SSN, "priority": 10,
            "pattern": r'(?:'
                       r'\b\d{3}[-\s.]\d{2}[-\s.]\d{4}\b|' # Standard SSN with delimiters
                       r'\b\d{9}\b(?=\D|$)|\b' # SSN without delimiters (ensure not part of longer number)
                       r'(?:ssn|social security(?: number| #)?)(?: is|:| =|: =|\s)\s*["\']?\d{3}[-\s.]?\d{2}[-\s.]?\d{4}["\']?|' # SSN with context
                       r'["\']?\w*(?:ssn|social_security|socialSecurity|social_security_number)["\']?\s*(?:=|:)\s*["\']?\d{3}[-\s.]?\d{2}[-\s.]?\d{4}["\']?|' # Code assignment
                       r'\.(?:ssn|social_security|socialSecurity|social_security_number)\s*=\s*["\']?\d{3}[-\s.]?\d{2}[-\s.]?\d{4}["\']?|' # Attribute access
                       r'["\'](?:ssn|social_security|socialSecurity|social_security_number)["\']?\s*:\s*["\']?\d{3}[-\s.]?\d{2}[-\s.]?\d{4}["\']?' # Dictionary
                       r')',
            "flags": re.IGNORECASE
        },
        {
            "name": "Phone", "type": PHIType.PHONE, "priority": 10,
            # Avoids matching numbers within words, allows optional country code, various delimiters
            "pattern": r'(?<!\w)(?:(?:\+\d{1,3}[\s.-]?)?(?:\(?\d{3}\)?[\s.-]?\d{3}[\s.-]?\d{4}))(?!\w|\d)',
            "flags": re.IGNORECASE
        },
         {
            "name": "MRN", "type": PHIType.MRN, "priority": 10,
            "pattern": r'\b(?:MRN|Medical Record Number|Patient ID|MR)[:\s#]*[A-Za-z0-9_-]{4,15}\b',
            "flags": re.IGNORECASE
        },
        # Medium Priority
        {
            "name": "Address", "type": PHIType.ADDRESS, "priority": 9,
            # Requires number, street name, common suffix. Avoids trailing numbers (like zip).
            "pattern": r'\b\d{1,6}\s+(?:[A-Za-z0-9\s.,-]+?)\b(?:Avenue|Lane|Road|Boulevard|Drive|Street|Ave|Ln|Rd|Blvd|Dr|St|Court|Ct|Place|Pl|Circle|Cir)\b\.?(?!\s*\d)',
            "flags": re.IGNORECASE
        },
        {
            "name": "Credit Card", "type": PHIType.CREDIT_CARD, "priority": 8,
            "pattern": r'\b(?:4[0-9]{3}[\s-]?[0-9]{4}[\s-]?[0-9]{4}[\s-]?[0-9]{4}|5[1-5][0-9]{2}[\s-]?[0-9]{4}[\s-]?[0-9]{4}[\s-]?[0-9]{4}|3[47][0-9]{2}[\s-]?[0-9]{6}[\s-]?[0-9]{5}|6(?:011|5[0-9]{2})[\s-]?[0-9]{4}[\s-]?[0-9]{4}[\s-]?[0-9]{4})\b'
        },
        {
            "name": "Email", "type": PHIType.EMAIL, "priority": 8,
            "pattern": r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        },
        {
            "name": "Policy Number", "type": PHIType.POLICY_NUMBER, "priority": 7,
            "pattern": r'\b(?:Policy|Insurance|Account|Member)(?:\s+Number|\s+ID)?[:\s#]*[A-Za-z0-9_-]{4,20}\b',
             "flags": re.IGNORECASE
        },
         {
            "name": "Financial Account", "type": PHIType.ACCOUNT_NUMBER, "priority": 7,
            "pattern": r'\b(?:Account|Acct)\s*(?:Number|No|#)?[:\s]*\d{6,16}\b',
             "flags": re.IGNORECASE
        },
         {
            "name": "License Number", "type": PHIType.LICENSE_NUMBER, "priority": 7,
             # Generic pattern, might need refinement for specific license types
            "pattern": r'\b(?:License|Lic|Driver\'?s License|DL)[:\s#]*[A-Za-z0-9]{6,15}\b',
             "flags": re.IGNORECASE
        },
        # Lower Priority / Context-Dependent
        {
            "name": "DOB", "type": PHIType.DOB, "priority": 6,
             "pattern": r'(?:'
                        r'\b(?:(?:dob|date of birth|birth date|birthdate|born on|born|birth)(?: is|:| =|: =|\s)\s*)?' # Context words
                        r'["\']?'
                        r'(?:' # Date formats
                            r'(?:(?:0?[1-9]|1[0-2])[/\-.](?:0?[1-9]|[12]\d|3[01])[/\-.]\d{2,4})|' # MM/DD/YYYY or M/D/YY etc.
                            r'(?:\d{4}[/\-.](?:0?[1-9]|1[0-2])[/\-.](?:0?[1-9]|[12]\d|3[01]))|' # YYYY/MM/DD
                            r'(?:(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*[\s.,-]+\d{1,2}(?:st|nd|rd|th)?[\s.,-]+\d{2,4})|' # Month DD, YYYY
                            r'(?:\d{1,2}(?:st|nd|rd|th)?[\s.,-]+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*[\s.,-]+\d{2,4})' # DD Month, YYYY
                        r')'
                        r'["\']?\b'
                        r')',
            "flags": re.IGNORECASE
        },
         {
            "name": "Age", "type": PHIType.AGE, "priority": 5,
            # Detect ages over 89, or explicit age mentions
            "pattern": r'\b(?:age|aged)\s+(?:9\d|[1-9]\d{2,})\b|\b(?:9\d|[1-9]\d{2,})\s+years?(?:\s+old)?\b',
            "flags": re.IGNORECASE
        },
        {
            "name": "Name", "type": PHIType.NAME, "priority": 4, "context_dependent": True,
            # Matches Title Caps Name (e.g., John Smith), Dr. Name, etc. Requires context check later.
            "pattern": r'\b(?:(?:[A-Z][a-z\'-]+){1,3}\s+(?:[A-Z][a-z\'-]+){1,3}|(?:Dr|Mr|Mrs|Ms)\.?\s+[A-Z][a-z\'-]+(?:\s+[A-Z][a-z\'-]+)?)\b'
        },
         {
            "name": "Date", "type": PHIType.DATE, "priority": 3, "context_dependent": True,
            # Generic date patterns, rely heavily on context
             "pattern": r'\b(?:\d{1,2}[-/\\.]\d{1,2}[-/\\.]\d{2,4}|\d{4}[-/\\.]\d{1,2}[-/\\.]\d{1,2})\b',
             "flags": re.IGNORECASE
        },
        {
            "name": "IP Address", "type": PHIType.IP_ADDRESS, "priority": 5,
            "pattern": r'\b((?:[0-9]{1,3}\.){3}[0-9]{1,3})\b' # Basic IPv4
        },
         {
            "name": "URL", "type": PHIType.URL, "priority": 2, "context_dependent": True,
             # Basic URL pattern, context needed to see if it contains identifiers
            "pattern": r'\b(?:https?://|www\.)[^\s/$.?#].[^\s]*\b',
             "flags": re.IGNORECASE
        },
    ]

    # Medical context terms from enhanced_phi_detector.py
    _CONTEXT_KEYWORDS: Set[str] = {
        "diagnosis", "condition", "patient", "prescribed", "medication",
        "treatment", "symptoms", "doctor", "physician", "clinic", "hospital",
        "appointment", "visit", "admitted", "discharged", "therapy", "assessment",
        "medical record", "health", "insurance", "claim", "subscriber", "beneficiary"
    }

    # Code context patterns from enhanced_phi_detector.py
    _CODE_CONTEXT_PATTERNS: Dict[str, str] = {
        # Detects assignments like ssn = "...", dob = '...' etc.
        'variable_assignment': r'(?:\b|_)(?:ssn|social_security|socialSecurity|dob|date_of_birth|dateOfBirth|birth_date|birthDate|mrn|medical_record|patient_id|email|phone|address)\s*=\s*["\'].*?["\']',
        # Detects dictionary assignments like "ssn": "...", 'dob': '...'
        'dict_assignment': r'["\'](?:ssn|social_security|dob|date_of_birth|dateOfBirth|birth_date|mrn|email|phone|address)["\']\s*:\s*["\'].*?["\']',
        # Detects PHI-like patterns within comments
        'comments': r'(?:#|//|/\*).*?(?:' + '|'.join([p['pattern'] for p in _PATTERNS_DEFINITIONS if p['priority'] >= 6]) + r')',
        # Detects PHI-like patterns in multiline strings (less precise)
        'multiline_strings': r'("""|\'\'\').*?(?:' + '|'.join([p['pattern'] for p in _PATTERNS_DEFINITIONS if p['priority'] >= 6]) + r').*?(\1)',
        # Detects default values in function signatures (less precise)
        'method_parameters': r'def\s+\w+\([^)]*\b(?:ssn|dob|birth_date|email|phone)\b\s*=\s*["\'].*?["\'][^)]*\)',
    }
    
    # Compiled patterns stored for efficiency (Instance attributes)
    _compiled_patterns: List[Dict[str, Any]]
    _compiled_code_patterns: Dict[str, Pattern]

    def __init__(self, custom_patterns_definitions: Optional[List[Dict[str, Any]]] = None):
        """Initialize the PHI service, compiling patterns."""
        self._compile_patterns(custom_patterns_definitions)
        logger.info(f"PHIService initialized with {len(self._compiled_patterns)} base patterns.")

    def _compile_patterns(self, custom_patterns_definitions: Optional[List[Dict[str, Any]]]):
        """Compile base and custom regex patterns."""
        all_definitions = self._PATTERNS_DEFINITIONS[:] # Copy base definitions
        if custom_patterns_definitions:
            # Simple merge, assumes custom patterns have unique names or override base ones
            # A more robust merge could handle conflicts based on priority or flags
            all_definitions.extend(custom_patterns_definitions)
            logger.info(f"Added {len(custom_patterns_definitions)} custom PHI patterns.")

        self._compiled_patterns = []
        for p_def in all_definitions:
            try:
                flags = p_def.get("flags", 0)
                compiled = re.compile(p_def["pattern"], flags)
                self._compiled_patterns.append({**p_def, "compiled": compiled})
            except re.error as e:
                logger.error(f"Invalid regex pattern for '{p_def.get('name', 'UNKNOWN')}': {p_def.get('pattern')}. Error: {e}")

        # Sort compiled patterns by priority (desc) for processing order
        self._compiled_patterns.sort(key=lambda p: p.get("priority", 0), reverse=True)

        # Compile code context patterns
        self._compiled_code_patterns = {}
        for name, pattern_str in self._CODE_CONTEXT_PATTERNS.items():
             try:
                 # Add IGNORECASE and DOTALL/MULTILINE where appropriate for code patterns
                 flags = re.IGNORECASE
                 if name in ['comments', 'multiline_strings', 'method_parameters']:
                      flags |= re.MULTILINE
                 if name == 'multiline_strings':
                      flags |= re.DOTALL
                 self._compiled_code_patterns[name] = re.compile(pattern_str, flags)
             except re.error as e:
                 logger.error(f"Invalid code context regex pattern for '{name}': {pattern_str}. Error: {e}")

    # --- Detection Methods ---

    def contains_phi(self, text: str, sensitivity: str = DEFAULT_SENSITIVITY) -> bool:
        """
        Check if text likely contains PHI based on sensitivity level.

        Args:
            text: Text to check.
            sensitivity: Detection sensitivity ('low', 'medium', 'high').

        Returns:
            True if PHI is likely present, False otherwise.
        """
        # Use detect_phi which incorporates sensitivity and context
        # Check if the list of detected PHI is non-empty
        return bool(self.detect_phi(text, sensitivity))

    def detect_phi(self, text: str, sensitivity: str = DEFAULT_SENSITIVITY) -> List[Tuple[PHIType, str, int, int]]:
        """
        Detect all instances of PHI in the text based on sensitivity.

        Args:
            text: Text to scan.
            sensitivity: Detection sensitivity.

        Returns:
            List of tuples: (PHIType, matched_text, start_index, end_index)
        """
        if not text or not isinstance(text, str):
             return []

        matches_found = []
        text_length = len(text)
        has_context = self._has_medical_context(text)

        # 1. Check code context patterns (highest priority)
        for name, compiled_pattern in self._compiled_code_patterns.items():
             for match in compiled_pattern.finditer(text):
                 start, end = match.start(), match.end()
                 # Heuristic mapping to PHIType based on pattern name/content
                 phi_type = self._map_code_context_to_phi_type(name, match.group(0))
                 matches_found.append({
                     "start": start, "end": end, "phi_type": phi_type,
                     "matched_text": match.group(0), "priority": 11, # Assign highest priority
                     "length": end - start, "source": f"code_context:{name}"
                 })

        # 2. Check standard patterns based on sensitivity
        for p_info in self._compiled_patterns:
            p_type = p_info["type"]
            p_priority = p_info.get("priority", 0)
            p_context_dependent = p_info.get("context_dependent", False)
            p_compiled = p_info["compiled"]

            should_check = self._should_check_pattern(p_priority, p_context_dependent, sensitivity, has_context)

            if should_check:
                 for match in p_compiled.finditer(text):
                      start, end = max(0, match.start()), min(text_length, match.end())
                      if start < end:
                           # Apply additional filters if necessary (e.g., for names without context)
                           if self._is_false_positive(p_type, match.group(0), has_context, sensitivity):
                                continue

                           matches_found.append({
                               "start": start, "end": end, "phi_type": p_type,
                               "matched_text": match.group(0), "priority": p_priority,
                               "length": end - start, "source": f"pattern:{p_info['name']}"
                           })

        # 3. Resolve overlaps
        resolved_matches = self._resolve_overlaps(matches_found)

        # 4. Format output
        return [(m["phi_type"], m["matched_text"], m["start"], m["end"]) for m in resolved_matches]

    # --- Sanitization Methods ---

    def sanitize(self, data: Any, sensitivity: str = DEFAULT_SENSITIVITY, replacement: Optional[str] = None) -> Any:
        """
        Sanitize potential PHI from any data structure (str, dict, list).

        Args:
            data: Data to sanitize.
            sensitivity: Detection sensitivity for identifying PHI.
            replacement: Custom replacement string template (e.g., "[HIDDEN]").
                         If None, uses DEFAULT_REPLACEMENT_TEMPLATE. Must contain {phi_type}.

        Returns:
            Sanitized data structure.
        """
        # Ensure replacement template is valid if provided
        if replacement and "{phi_type}" not in replacement:
             logger.warning(f"Custom replacement template '{replacement}' is missing " + 
                           "{phi_type}. Using default.")
             replacement = None # Fallback to default

        if data is None:
            return None

        if isinstance(data, str):
            return self.sanitize_text(data, sensitivity, replacement)
        elif isinstance(data, dict):
            # Sanitize keys as well, assuming keys could potentially be PHI
            sanitized_dict = {}
            for k, v in data.items():
                sanitized_key = self.sanitize(k, sensitivity, replacement) if isinstance(k, str) else k
                sanitized_dict[sanitized_key] = self.sanitize(v, sensitivity, replacement)
            return sanitized_dict
        elif isinstance(data, (list, tuple, set)):
            sanitized_items = [self.sanitize(item, sensitivity, replacement) for item in data]
            if isinstance(data, tuple):
                return tuple(sanitized_items)
            elif isinstance(data, set):
                 # Note: Sanitization might cause duplicate "[REDACTED]" values in sets
                return set(sanitized_items)
            else: # list
                return sanitized_items
        else:
            # Non-sanitizable types (int, float, bool, bytes, etc.)
            # Consider whether to sanitize bytes if needed
            return data

    def sanitize_text(self, text: str, sensitivity: str = DEFAULT_SENSITIVITY, replacement: Optional[str] = None) -> str:
        """
        Sanitize PHI from a text string.

        Args:
            text: Text to sanitize.
            sensitivity: Detection sensitivity.
            replacement: Custom replacement template.

        Returns:
            Sanitized text.
        """
        if not text or not isinstance(text, str):
            return text

        # Use detect_phi which already handles sensitivity and overlaps
        detected_phi = self.detect_phi(text, sensitivity)
        if not detected_phi:
            return text

        # DEBUG: Log detected emails
        emails_detected = [(t, s, e) for typ, t, s, e in detected_phi if typ == PHIType.EMAIL]
        if emails_detected:
            logger.info(f"---> Sanitize_text: Detected EMAIL(s) in text: '{text[:100]}...' - Matches: {emails_detected}")

        # Sort matches by start index in reverse to avoid index shifting during replacement
        # detect_phi already returns resolved, sorted matches - re-sorting might be redundant if detect_phi guarantees order
        detected_phi.sort(key=lambda x: x[2], reverse=True)

        sanitized_text = list(text)
        template = replacement or self.DEFAULT_REPLACEMENT_TEMPLATE
        # Ensure template is valid
        if "{phi_type}" not in template:
             template = self.DEFAULT_REPLACEMENT_TEMPLATE

        for phi_type, matched_str, start, end in detected_phi:
            # Use the helper to get the formatted replacement value
            replacement_value = self._get_replacement_value(phi_type, template)
            # DEBUG: Log replacement action for emails
            if phi_type == PHIType.EMAIL:
                logger.info(f"---> Sanitize_text: Replacing email '{matched_str}' at [{start}:{end}] with '{replacement_value}'")
            sanitized_text[start:end] = list(replacement_value)

        final_sanitized = "".join(sanitized_text)
        # Optional: Post-processing step to clean up adjacent redactions, e.g., "[REDACTED NAME] [REDACTED ADDRESS]" -> "[REDACTED INFO]"
        # final_sanitized = re.sub(r'(\[REDACTED [A-Z_]+\])(\s+\1)+', r'\1', final_sanitized) # Example cleanup
        return final_sanitized

    # --- Helper Methods ---

    def _should_check_pattern(self, priority: int, context_dependent: bool, sensitivity: str, has_context: bool) -> bool:
         """Determine if a pattern should be checked based on sensitivity and context."""
         if sensitivity == "low":
             # Only high-priority, non-context patterns
             return priority >= 8 and not context_dependent
         elif sensitivity == "medium":
             # Medium/high priority non-context, or context-dependent if context exists
             return (priority >= 6 and not context_dependent) or (context_dependent and has_context)
         elif sensitivity == "high":
             # Check all patterns
             return True
         return False # Default case

    def _is_false_positive(self, phi_type: PHIType, matched_text: str, has_context: bool, sensitivity: str) -> bool:
        """Apply additional filters to reduce false positives, especially for context-dependent types."""
        # Example: Filter common words misidentified as names when no context is present
        if phi_type == PHIType.NAME and not has_context and sensitivity == "medium":
             # List of common English words, days, months etc. that are often capitalized but not names
             common_non_names = {
                 "tuesday", "january", "february", "march", "april", "may", "june", "july", 
                 "august", "september", "october", "november", "december",
                 "monday", "wednesday", "thursday", "friday", "saturday", "sunday",
                 "spring", "summer", "autumn", "winter", "today", "tomorrow", "yesterday",
                 "north", "south", "east", "west" 
                 # Add more common words, titles, or locations if needed
             }
             if matched_text.lower() in common_non_names:
                 return True
        # Can add more filters for other types like DATE if needed
        return False
        
    def _map_code_context_to_phi_type(self, pattern_name: str, matched_text: str) -> PHIType:
        """Heuristic mapping from code context pattern match to PHIType."""
        matched_lower = matched_text.lower()
        if "ssn" in matched_lower or "social" in matched_lower: return PHIType.SSN
        if "dob" in matched_lower or "birth" in matched_lower: return PHIType.DOB
        if "mrn" in matched_lower or "patient_id" in matched_lower or "medical_record" in matched_lower: return PHIType.MRN
        if "email" in matched_lower: return PHIType.EMAIL
        if "phone" in matched_lower: return PHIType.PHONE
        if "address" in matched_lower: return PHIType.ADDRESS
        if "credit" in matched_lower or "card" in matched_lower: return PHIType.CREDIT_CARD
        if "policy" in matched_lower or "insurance" in matched_lower: return PHIType.POLICY_NUMBER
        if "account" in matched_lower: return PHIType.ACCOUNT_NUMBER
        if "license" in matched_lower: return PHIType.LICENSE_NUMBER
        # Add more specific mappings if code patterns become more granular
        return PHIType.OTHER # Default fallback

    def _has_medical_context(self, text: str) -> bool:
        """Check if text contains keywords indicating a medical context."""
        if not text or not isinstance(text, str):
             return False
        text_lower = text.lower()
        return any(keyword in text_lower for keyword in self._CONTEXT_KEYWORDS)

    def _contains_phi_in_code_context(self, text: str) -> bool:
        """Check if text matches any code-specific PHI patterns."""
        if not text or not isinstance(text, str):
             return False
        return any(pattern.search(text) for pattern in self._compiled_code_patterns.values())

    def _resolve_overlaps(self, matches: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Resolve overlapping PHI matches based on priority and length."""
        if not matches:
            return []

        # Sort by priority (desc), then length (desc), then start index (asc)
        matches.sort(key=lambda m: (m.get("priority", 0), m.get("length", 0), -m["start"]), reverse=True)

        text_length = max(m["end"] for m in matches) if matches else 0
        covered = [False] * text_length # Track covered character indices
        final_matches = []

        for match in matches:
            start, end = match["start"], match["end"]
            # Check if any part of this match interval is already covered by a higher priority match
            is_overlapped = any(covered[i] for i in range(start, end))

            if not is_overlapped:
                # Mark this interval as covered
                for i in range(start, end):
                    if i < text_length: # Boundary check
                         covered[i] = True
                final_matches.append(match)

        # Return sorted by original start position for sequential processing if needed elsewhere
        return sorted(final_matches, key=lambda m: m['start'])

    def _get_replacement_value(self, phi_type: PHIType, custom_template: Optional[str] = None) -> str:
        """Generate the replacement string for a given PHI type."""
        template = custom_template or self.DEFAULT_REPLACEMENT_TEMPLATE
        # Ensure template is valid
        if "{phi_type}" not in template:
             template = self.DEFAULT_REPLACEMENT_TEMPLATE
        return template.format(phi_type=phi_type.name)

# --- Service Instance (Optional Singleton) ---
# You might want to instantiate this once and reuse it, potentially via dependency injection.
# phi_service_instance = PHIService()
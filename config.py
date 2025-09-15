"""Configuration for Telegram appointment listener bot."""

import re
from typing import List, Pattern

class Config:
    """Configuration class for the appointment listener bot."""
    
    # Target channel to monitor
    TARGET_CHANNEL = "@Visasoon"
    
    # Country and city patterns to monitor
    # Format: "Country · City"
    TARGET_PATTERNS = [
        "France · Edingburgh",
        "France · London",
        "Cyprus · London",
        "Cyprus · Manchester",
    ]
    
    @classmethod
    def get_compiled_patterns(cls) -> List[Pattern]:
        """Get compiled regex patterns for country/city combinations."""
        patterns = []
        for pattern in cls.TARGET_PATTERNS:
            # Escape special regex characters and create pattern
            escaped_pattern = re.escape(pattern)
            # Compile with case-insensitive matching
            compiled_pattern = re.compile(escaped_pattern, re.IGNORECASE)
            patterns.append(compiled_pattern)
        return patterns
    
    @classmethod
    def get_appointment_message_pattern(cls) -> Pattern:
        """Get regex pattern to identify appointment messages."""
        # Pattern to match messages containing appointment dates and times
        appointment_pattern = r"Appointment Date:\s*\|.*\[\d{2}:\d{2}"
        return re.compile(appointment_pattern, re.MULTILINE | re.DOTALL)
    
    @classmethod
    def add_target_pattern(cls, pattern: str) -> None:
        """Add a new target pattern to monitor."""
        if pattern not in cls.TARGET_PATTERNS:
            cls.TARGET_PATTERNS.append(pattern)
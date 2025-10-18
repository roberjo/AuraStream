"""Input validation utilities."""

import re
from typing import List, Dict, Any


class InputValidator:
    """Validates input data for security and correctness."""
    
    # Malicious patterns
    SQL_INJECTION_PATTERNS = [
        r'(\b(SELECT|INSERT|UPDATE|DELETE|DROP|CREATE|ALTER|EXEC|UNION)\b)',
        r'(\b(OR|AND)\s+\d+\s*=\s*\d+)',
        r'(\b(OR|AND)\s+\w+\s*=\s*\w+)'
    ]
    
    XSS_PATTERNS = [
        r'<script[^>]*>.*?</script>',
        r'javascript:',
        r'on\w+\s*=',
        r'<iframe[^>]*>',
        r'<object[^>]*>',
        r'<embed[^>]*>'
    ]
    
    COMMAND_INJECTION_PATTERNS = [
        r'[;&|`$]',
        r'\b(cat|ls|pwd|whoami|id|uname)\b',
        r'\b(ping|nslookup|traceroute)\b'
    ]
    
    @classmethod
    def validate_text_security(cls, text: str) -> Dict[str, Any]:
        """
        Validate text for security threats.
        
        Args:
            text: Text to validate
            
        Returns:
            Validation results
        """
        threats = []
        
        # Check for SQL injection
        for pattern in cls.SQL_INJECTION_PATTERNS:
            if re.search(pattern, text, re.IGNORECASE):
                threats.append({
                    'type': 'sql_injection',
                    'pattern': pattern,
                    'severity': 'high'
                })
        
        # Check for XSS
        for pattern in cls.XSS_PATTERNS:
            if re.search(pattern, text, re.IGNORECASE):
                threats.append({
                    'type': 'xss',
                    'pattern': pattern,
                    'severity': 'high'
                })
        
        # Check for command injection
        for pattern in cls.COMMAND_INJECTION_PATTERNS:
            if re.search(pattern, text, re.IGNORECASE):
                threats.append({
                    'type': 'command_injection',
                    'pattern': pattern,
                    'severity': 'critical'
                })
        
        return {
            'is_safe': len(threats) == 0,
            'threats': threats,
            'threat_count': len(threats)
        }
    
    @classmethod
    def validate_api_key(cls, api_key: str) -> bool:
        """
        Validate API key format.
        
        Args:
            api_key: API key to validate
            
        Returns:
            True if valid format
        """
        if not api_key or not isinstance(api_key, str):
            return False
        
        # API key should be alphanumeric and 32-64 characters
        if not re.match(r'^[a-zA-Z0-9]{32,64}$', api_key):
            return False
        
        return True
    
    @classmethod
    def validate_language_code(cls, language_code: str) -> bool:
        """
        Validate language code format.
        
        Args:
            language_code: Language code to validate
            
        Returns:
            True if valid format
        """
        if not language_code or not isinstance(language_code, str):
            return False
        
        # Language code should be 2-3 characters
        if not re.match(r'^[a-z]{2,3}$', language_code.lower()):
            return False
        
        return True
    
    @classmethod
    def validate_job_id(cls, job_id: str) -> bool:
        """
        Validate job ID format.
        
        Args:
            job_id: Job ID to validate
            
        Returns:
            True if valid format
        """
        if not job_id or not isinstance(job_id, str):
            return False
        
        # Job ID should be UUID format
        uuid_pattern = r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$'
        if not re.match(uuid_pattern, job_id.lower()):
            return False
        
        return True

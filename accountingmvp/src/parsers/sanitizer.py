"""Input sanitization utilities for security."""
import re


def sanitize_csv_value(value: str) -> str:
    """
    Prevents CSV injection by neutralizing dangerous formula characters.
    Ref: https://owasp.org/www-community/attacks/CSV_Injection
    """
    if not value:
        return ""
        
    # Dangerous prefixes that trigger formula execution
    dangerous_prefixes = ('=', '+', '-', '@', '\t', '\r')
    
    clean_value = value.strip()
    
    if clean_value.startswith(dangerous_prefixes):
        # Prefix with single quote to force text interpretation
        return f"'{clean_value}"
    
    return clean_value


def safe_filename(filename: str) -> str:
    """
    Removes path traversal and other dangerous characters from filenames.
    
    Security considerations:
    - Remove ../ path traversal attempts
    - Remove absolute path prefixes
    - Replace special characters with underscores
    - Collapse multiple underscores
    """
    # First, remove any path traversal sequences
    clean = filename
    
    # Remove ../ and ..\\ sequences
    clean = re.sub(r'\.\.[\\/]', '', clean)
    
    # Remove leading slashes (absolute paths)
    clean = re.sub(r'^[\\/]+', '', clean)
    
    # Replace remaining special characters with underscores
    clean = re.sub(r'[^a-zA-Z0-9_.-]', '_', clean)
    
    # Collapse multiple underscores
    clean = re.sub(r'_+', '_', clean)
    
    # Remove leading/trailing underscores
    clean = clean.strip('_')
    
    # If empty after cleaning, use default
    if not clean:
        clean = "untitled"
    
    return clean

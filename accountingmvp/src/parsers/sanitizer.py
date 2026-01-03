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
    """Removes path traversal characters."""
    return re.sub(r'[^a-zA-Z0-9_.-]', '_', filename)

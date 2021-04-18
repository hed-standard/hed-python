

class HedError(Exception):
    """Exception raised when a file cannot be parsed due to being malformed, file IO, etc."""
    def __init__(self, error_type, message, error_code=None, severity=1):
        self.error_type = error_type
        self.message = message
        self.error_code = error_code
        self.severity = severity

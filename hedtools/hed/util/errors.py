

class SchemaError(Exception):
    def __init__(self, message):
        self.message = f"SchemaError: {message}"

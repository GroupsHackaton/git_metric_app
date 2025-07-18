class GitHubServiceError(Exception):
    """Custom exception for errors related to the GitHub Service."""
    def __init__(self, message: str, status_code: int = 500):
        self.message = message
        self.status_code = status_code
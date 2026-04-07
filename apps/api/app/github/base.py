class GitHubExecutionError(Exception):
    pass


class GitHubExecutionProvider:
    def run(self, request_type: str, repo: str, title: str, objective: str, context: dict) -> dict:
        raise NotImplementedError

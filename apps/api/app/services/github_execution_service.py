from app.core.config import settings
from app.github.providers.readonly_provider import GitHubReadOnlyProvider
from app.github.providers.proposal_provider import GitHubProposalProvider
from app.github.providers.write_request_provider import GitHubWriteRequestProvider


class GitHubExecutionService:
    def __init__(self):
        self.readonly_provider = GitHubReadOnlyProvider()
        self.proposal_provider = GitHubProposalProvider()
        self.write_request_provider = GitHubWriteRequestProvider()

    def capabilities(self) -> dict:
        return {
            "enabled": settings.GITHUB_EXECUTION_ENABLED,
            "mode": settings.GITHUB_EXECUTION_MODE,
            "default_repo": settings.GITHUB_DEFAULT_REPO,
            "supported_request_types": [
                "repo_inspect",
                "branch_plan",
                "patch_proposal",
                "pr_draft",
                "repo_write_request",
            ],
        }

    def run(self, request_type: str, repo: str, title: str, objective: str, context: dict) -> dict:
        if request_type == "repo_inspect":
            return self.readonly_provider.run(request_type, repo, title, objective, context)

        if request_type in {"branch_plan", "patch_proposal", "pr_draft"}:
            return self.proposal_provider.run(request_type, repo, title, objective, context)

        if request_type == "repo_write_request":
            return self.write_request_provider.run(request_type, repo, title, objective, context)

        raise ValueError(f"Unsupported GitHub request type: {request_type}")

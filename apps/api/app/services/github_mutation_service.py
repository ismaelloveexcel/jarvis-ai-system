from app.core.config import settings
from app.github_mutation.providers.stub_provider import GitHubMutationStubProvider
from app.github_mutation.providers.live_provider import GitHubMutationLiveProvider


class GitHubMutationService:
    def __init__(self):
        if settings.GITHUB_MUTATION_ENABLED and settings.GITHUB_MUTATION_MODE == "live":
            self.provider = GitHubMutationLiveProvider()
        else:
            self.provider = GitHubMutationStubProvider()

    def capabilities(self) -> dict:
        return {
            "enabled": settings.GITHUB_MUTATION_ENABLED,
            "mode": settings.GITHUB_MUTATION_MODE,
            "default_base_branch": settings.GITHUB_DEFAULT_BASE_BRANCH,
            "default_draft_pr": settings.GITHUB_DEFAULT_DRAFT_PR,
            "supported_request_types": [
                "create_branch",
                "create_patch_artifact",
                "create_pr_draft",
                "execute_repo_write",
                "merge_request",
            ],
        }

    def run(self, request_type: str, repo: str, title: str, objective: str, context: dict) -> dict:
        return self.provider.run(
            request_type=request_type,
            repo=repo,
            title=title,
            objective=objective,
            context=context,
        )

from app.github_mutation.base import GitHubMutationProvider
from app.core.config import settings


class GitHubMutationLiveProvider(GitHubMutationProvider):
    def _ensure_repo_allowed(self, repo: str):
        allowed = [r.strip() for r in settings.GITHUB_ALLOWED_WRITE_REPOS.split(",") if r.strip()]
        if not settings.GITHUB_MUTATION_LIVE_ENABLED:
            raise ValueError("Live GitHub mutation is disabled.")
        if not settings.GITHUB_TOKEN:
            raise ValueError("Missing GITHUB_TOKEN for live mutation mode.")
        if allowed and repo not in allowed:
            raise ValueError(f"Repo '{repo}' is not in GITHUB_ALLOWED_WRITE_REPOS.")

    def run(self, request_type: str, repo: str, title: str, objective: str, context: dict) -> dict:
        self._ensure_repo_allowed(repo)

        base_branch = context.get("base_branch", settings.GITHUB_DEFAULT_BASE_BRANCH)
        feature_branch = context.get("feature_branch", "feature/live-mutation")
        pr_title = context.get("pr_title", f"Draft PR: {title}")
        artifact_id = context.get("artifact_id")

        if base_branch in {"main", "master"} and request_type == "execute_repo_write":
            if not feature_branch or feature_branch in {"main", "master"}:
                raise ValueError("execute_repo_write requires a non-default feature branch.")

        if request_type == "create_branch":
            return {
                "status": "success",
                "execution_mode": "github_mutation_live",
                "request_type": request_type,
                "repo": repo,
                "branch": feature_branch,
                "base_branch": base_branch,
                "summary": f"Live-safe branch creation prepared for {feature_branch} from {base_branch}.",
            }

        if request_type == "create_patch_artifact":
            return {
                "status": "success",
                "execution_mode": "github_mutation_live",
                "request_type": request_type,
                "repo": repo,
                "artifact_id": artifact_id,
                "summary": "Live-safe patch artifact reference accepted.",
            }

        if request_type == "create_pr_draft":
            return {
                "status": "success",
                "execution_mode": "github_mutation_live",
                "request_type": request_type,
                "repo": repo,
                "pr": {
                    "title": pr_title,
                    "base_branch": base_branch,
                    "feature_branch": feature_branch,
                    "draft": settings.GITHUB_DEFAULT_DRAFT_PR,
                },
                "artifact_id": artifact_id,
                "summary": "Live-safe draft PR creation prepared.",
            }

        if request_type == "execute_repo_write":
            return {
                "status": "success",
                "execution_mode": "github_mutation_live",
                "request_type": request_type,
                "repo": repo,
                "write_plan": {
                    "base_branch": base_branch,
                    "feature_branch": feature_branch,
                    "artifact_id": artifact_id,
                    "requested_changes": context.get("requested_changes", []),
                },
                "summary": "Live-safe repo write execution prepared on feature branch only.",
            }

        if request_type == "merge_request":
            return {
                "status": "blocked",
                "execution_mode": "github_mutation_live",
                "request_type": request_type,
                "repo": repo,
                "summary": "Merge remains blocked by policy in Phase 9.",
            }

        raise ValueError(f"Unsupported mutation request type: {request_type}")

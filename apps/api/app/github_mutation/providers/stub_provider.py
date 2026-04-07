from app.github_mutation.base import GitHubMutationProvider
from app.core.config import settings


class GitHubMutationStubProvider(GitHubMutationProvider):
    def run(self, request_type: str, repo: str, title: str, objective: str, context: dict) -> dict:
        base_branch = context.get("base_branch", settings.GITHUB_DEFAULT_BASE_BRANCH)
        feature_branch = context.get("feature_branch", "feature/pending-mutation")
        pr_title = context.get("pr_title", f"Draft PR: {title}")

        if request_type == "create_branch":
            return {
                "status": "success",
                "execution_mode": "github_mutation_stub",
                "request_type": request_type,
                "repo": repo,
                "branch": feature_branch,
                "base_branch": base_branch,
                "summary": f"Stubbed branch creation prepared for {feature_branch} from {base_branch}.",
            }

        if request_type == "create_patch_artifact":
            return {
                "status": "success",
                "execution_mode": "github_mutation_stub",
                "request_type": request_type,
                "repo": repo,
                "artifact": {
                    "type": "patch",
                    "name": context.get("artifact_name", "proposed-change.patch"),
                    "requested_changes": context.get("requested_changes", []),
                },
                "summary": "Stubbed patch artifact created.",
            }

        if request_type == "create_pr_draft":
            return {
                "status": "success",
                "execution_mode": "github_mutation_stub",
                "request_type": request_type,
                "repo": repo,
                "pr": {
                    "title": pr_title,
                    "base_branch": base_branch,
                    "feature_branch": feature_branch,
                    "draft": settings.GITHUB_DEFAULT_DRAFT_PR,
                },
                "summary": "Stubbed draft PR created.",
            }

        if request_type == "execute_repo_write":
            return {
                "status": "success",
                "execution_mode": "github_mutation_stub",
                "request_type": request_type,
                "repo": repo,
                "write_plan": {
                    "base_branch": base_branch,
                    "feature_branch": feature_branch,
                    "requested_changes": context.get("requested_changes", []),
                },
                "summary": "Stubbed repo write workflow executed after approval.",
            }

        if request_type == "merge_request":
            return {
                "status": "blocked",
                "execution_mode": "github_mutation_stub",
                "request_type": request_type,
                "repo": repo,
                "summary": "Merge remains blocked by policy in Phase 7.",
            }

        raise ValueError(f"Unsupported mutation request type: {request_type}")

from app.github.base import GitHubExecutionProvider


class GitHubWriteRequestProvider(GitHubExecutionProvider):
    def run(self, request_type: str, repo: str, title: str, objective: str, context: dict) -> dict:
        return {
            "status": "success",
            "execution_mode": "github_write_request",
            "request_type": request_type,
            "repo": repo,
            "title": title,
            "objective": objective,
            "summary": "Write request prepared. Actual mutation must remain approval-gated.",
            "write_request": {
                "target_branch": context.get("target_branch", "main"),
                "proposed_branch": context.get("proposed_branch", "feature/pending-approval"),
                "requested_changes": context.get("requested_changes", []),
            }
        }

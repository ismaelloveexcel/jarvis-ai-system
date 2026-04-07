from app.github.base import GitHubExecutionProvider


class GitHubReadOnlyProvider(GitHubExecutionProvider):
    def run(self, request_type: str, repo: str, title: str, objective: str, context: dict) -> dict:
        return {
            "status": "success",
            "execution_mode": "github_readonly",
            "request_type": request_type,
            "repo": repo,
            "title": title,
            "objective": objective,
            "summary": f"Readonly GitHub execution completed for '{title}'.",
            "details": {
                "inspection_scope": context.get("inspection_scope", "default"),
                "note": "Phase 6 readonly workflow"
            }
        }

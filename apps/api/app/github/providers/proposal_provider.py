from app.github.base import GitHubExecutionProvider


class GitHubProposalProvider(GitHubExecutionProvider):
    def run(self, request_type: str, repo: str, title: str, objective: str, context: dict) -> dict:
        return {
            "status": "success",
            "execution_mode": "github_proposal",
            "request_type": request_type,
            "repo": repo,
            "title": title,
            "objective": objective,
            "summary": f"Proposal workflow completed for '{title}'.",
            "proposal": {
                "branch_name": context.get("branch_name", "feature/jarvis-proposal"),
                "change_plan": context.get("change_plan", [
                    "Inspect repository structure",
                    "Draft patch proposal",
                    "Prepare PR draft"
                ]),
                "pr_title": context.get("pr_title", f"Proposal: {title}"),
                "pr_body": context.get("pr_body", "This is a draft PR proposal generated in Phase 6."),
            }
        }

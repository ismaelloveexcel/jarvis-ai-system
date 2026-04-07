def github_repo_info_stub(repo: str) -> dict:
    return {
        "status": "success",
        "action": "github_repo_info_stub",
        "repo": repo,
        "note": "Phase 2 safe stub only. No live GitHub mutation is performed.",
        "mock_data": {
            "name": repo.split("/")[-1] if "/" in repo else repo,
            "owner": repo.split("/")[0] if "/" in repo else "unknown",
            "stars": 0,
            "language": "unknown",
            "description": "Stub response - connect to real GitHub API in Phase 3",
        },
    }

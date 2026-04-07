ALLOWED_HTTP_HOSTS = {
    "example.com",
    "httpbin.org",
    "jsonplaceholder.typicode.com",
}

APPROVAL_REQUIRED_ACTIONS = {
    "create_file",
}

BLOCKED_ACTIONS = {
    "github_mutation",
    "delete_file",
    "run_shell_command",
}

SAFE_WRITE_PREFIXES = [
    "example/",
    "notes/",
    "drafts/",
]

# Actions that are always allowed without approval
ALWAYS_ALLOWED_ACTIONS = {
    "read_file",
    "github_repo_info_stub",
}

APPROVAL_REQUIRED_EXECUTION_TYPES = {
    "repo_scaffold",
    "file_refactor",
}

ALWAYS_ALLOWED_EXECUTION_TYPES = {
    "code_generation",
    "bug_fix_plan",
}

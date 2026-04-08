from enum import Enum
from pydantic import BaseModel


class ActionName(str, Enum):
    READ_FILE = "read_file"
    CREATE_FILE = "create_file"
    DELETE_FILE = "delete_file"
    HTTP_REQUEST = "http_request"
    GITHUB_REPO_INFO_STUB = "github_repo_info_stub"
    GITHUB_MUTATION = "github_mutation"
    RUN_SHELL_COMMAND = "run_shell_command"


class PolicySet(BaseModel):
    allowed: frozenset[str]
    approval_required: frozenset[str]
    blocked: frozenset[str]


# --- Action policies ---
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

ALWAYS_ALLOWED_ACTIONS = {
    "read_file",
    "github_repo_info_stub",
}

ACTION_POLICY = PolicySet(
    allowed=frozenset(ALWAYS_ALLOWED_ACTIONS),
    approval_required=frozenset(APPROVAL_REQUIRED_ACTIONS),
    blocked=frozenset(BLOCKED_ACTIONS),
)

# --- Execution policies ---
APPROVAL_REQUIRED_EXECUTION_TYPES = {
    "repo_scaffold",
    "file_refactor",
}

ALWAYS_ALLOWED_EXECUTION_TYPES = {
    "code_generation",
    "bug_fix_plan",
}

EXECUTION_POLICY = PolicySet(
    allowed=frozenset(ALWAYS_ALLOWED_EXECUTION_TYPES),
    approval_required=frozenset(APPROVAL_REQUIRED_EXECUTION_TYPES),
    blocked=frozenset(),
)

# --- GitHub policies ---
ALWAYS_ALLOWED_GITHUB_TYPES = {
    "repo_inspect",
    "branch_plan",
    "patch_proposal",
    "pr_draft",
}

APPROVAL_REQUIRED_GITHUB_TYPES = {
    "repo_write_request",
}

APPROVAL_REQUIRED_GITHUB_MUTATION_TYPES = {
    "create_branch",
    "create_patch_artifact",
    "create_pr_draft",
    "execute_repo_write",
}

BLOCKED_GITHUB_MUTATION_TYPES = {
    "merge_request",
}

GITHUB_POLICY = PolicySet(
    allowed=frozenset(ALWAYS_ALLOWED_GITHUB_TYPES),
    approval_required=frozenset(APPROVAL_REQUIRED_GITHUB_TYPES),
    blocked=frozenset(),
)

GITHUB_MUTATION_POLICY = PolicySet(
    allowed=frozenset(),
    approval_required=frozenset(APPROVAL_REQUIRED_GITHUB_MUTATION_TYPES),
    blocked=frozenset(BLOCKED_GITHUB_MUTATION_TYPES),
)

# --- Ops policies ---
ALWAYS_ALLOWED_OPS_TYPES = {
    "maintenance_check",
    "runbook_lookup",
}

APPROVAL_REQUIRED_OPS_TYPES = {
    "deployment_request",
    "promote_environment",
    "rollback_request",
}

OPS_POLICY = PolicySet(
    allowed=frozenset(ALWAYS_ALLOWED_OPS_TYPES),
    approval_required=frozenset(APPROVAL_REQUIRED_OPS_TYPES),
    blocked=frozenset(),
)

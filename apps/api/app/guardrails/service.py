from urllib.parse import urlparse
from app.guardrails.policy import (
    ALLOWED_HTTP_HOSTS,
    ALWAYS_ALLOWED_ACTIONS,
    BLOCKED_ACTIONS,
    SAFE_WRITE_PREFIXES,
    APPROVAL_REQUIRED_EXECUTION_TYPES,
    ALWAYS_ALLOWED_EXECUTION_TYPES,
    ALWAYS_ALLOWED_GITHUB_TYPES,
    APPROVAL_REQUIRED_GITHUB_TYPES,
    APPROVAL_REQUIRED_GITHUB_MUTATION_TYPES,
    BLOCKED_GITHUB_MUTATION_TYPES,
    ALWAYS_ALLOWED_OPS_TYPES,
    APPROVAL_REQUIRED_OPS_TYPES,
)


class GuardrailResult(dict):
    pass


class GuardrailService:
    def evaluate(self, action_name: str, payload: dict) -> GuardrailResult:
        if action_name in BLOCKED_ACTIONS:
            return GuardrailResult({
                "decision": "blocked",
                "reason": f"Action '{action_name}' is blocked by policy.",
            })

        if action_name in ALWAYS_ALLOWED_ACTIONS:
            return GuardrailResult({"decision": "allow"})

        if action_name == "http_request":
            url = payload.get("url", "")
            hostname = urlparse(url).hostname or ""
            if hostname not in ALLOWED_HTTP_HOSTS:
                return GuardrailResult({
                    "decision": "blocked",
                    "reason": f"HTTP host '{hostname}' is not allowlisted.",
                })
            return GuardrailResult({"decision": "allow"})

        if action_name == "create_file":
            relative_path = payload.get("relative_path", "")
            if any(relative_path.startswith(prefix) for prefix in SAFE_WRITE_PREFIXES):
                return GuardrailResult({"decision": "allow"})
            return GuardrailResult({
                "decision": "approval_required",
                "reason": f"Writing to '{relative_path}' requires approval.",
            })

        return GuardrailResult({
            "decision": "blocked",
            "reason": f"Unknown or unapproved action '{action_name}'.",
        })

    def evaluate_execution(self, request_type: str, payload: dict) -> GuardrailResult:
        if request_type in ALWAYS_ALLOWED_EXECUTION_TYPES:
            return GuardrailResult({"decision": "allow"})

        if request_type in APPROVAL_REQUIRED_EXECUTION_TYPES:
            return GuardrailResult({
                "decision": "approval_required",
                "reason": f"Execution type '{request_type}' requires approval.",
            })

        return GuardrailResult({
            "decision": "blocked",
            "reason": f"Execution type '{request_type}' is not allowed.",
        })

    def evaluate_github_execution(self, request_type: str, payload: dict) -> GuardrailResult:
        if request_type in ALWAYS_ALLOWED_GITHUB_TYPES:
            return GuardrailResult({"decision": "allow"})

        if request_type in APPROVAL_REQUIRED_GITHUB_TYPES:
            return GuardrailResult({
                "decision": "approval_required",
                "reason": f"GitHub request type '{request_type}' requires approval.",
            })

        return GuardrailResult({
            "decision": "blocked",
            "reason": f"GitHub request type '{request_type}' is not allowed.",
        })

    def evaluate_github_mutation(self, request_type: str, payload: dict) -> GuardrailResult:
        if request_type in BLOCKED_GITHUB_MUTATION_TYPES:
            return GuardrailResult({
                "decision": "blocked",
                "reason": f"GitHub mutation '{request_type}' remains blocked by policy.",
            })

        if request_type in APPROVAL_REQUIRED_GITHUB_MUTATION_TYPES:
            return GuardrailResult({
                "decision": "approval_required",
                "reason": f"GitHub mutation '{request_type}' requires approval.",
            })

        return GuardrailResult({
            "decision": "blocked",
            "reason": f"GitHub mutation '{request_type}' is not allowed.",
        })

    def evaluate_ops(self, request_type: str, payload: dict) -> GuardrailResult:
        if request_type in ALWAYS_ALLOWED_OPS_TYPES:
            return GuardrailResult({"decision": "allow"})

        if request_type in APPROVAL_REQUIRED_OPS_TYPES:
            return GuardrailResult({
                "decision": "approval_required",
                "reason": f"Ops request '{request_type}' requires approval.",
            })

        return GuardrailResult({
            "decision": "blocked",
            "reason": f"Ops request '{request_type}' is not allowed.",
        })

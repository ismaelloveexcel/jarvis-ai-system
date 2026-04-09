import json
import logging
from urllib.parse import urlparse
from app.guardrails.policy import (
    ALLOWED_HTTP_HOSTS,
    APPROVAL_REQUIRED_ACTIONS,
    BLOCKED_ACTIONS,
    SAFE_WRITE_PREFIXES,
    ALWAYS_ALLOWED_ACTIONS,
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
    def __init__(self):
        self.logger = logging.getLogger("jarvis.guardrails")
        self.MAX_PAYLOAD_SIZE = 1_048_576  # 1MB
        self.MAX_CONTEXT_SIZE = 65_536  # 64KB

    def _check_payload_size(self, payload: dict, context: dict | None = None) -> GuardrailResult | None:
        """
        Check if payload and context objects exceed size limits.
        Returns GuardrailResult with blocked decision if limit exceeded, None otherwise.
        """
        payload_size = len(json.dumps(payload).encode('utf-8'))
        total_size = payload_size

        if payload_size > self.MAX_PAYLOAD_SIZE:
            self.logger.warning(
                "security_event",
                extra={
                    "event_type": "payload_size_exceeded",
                    "payload_size_bytes": payload_size,
                    "max_allowed": self.MAX_PAYLOAD_SIZE,
                    "exceeded_by_bytes": payload_size - self.MAX_PAYLOAD_SIZE,
                }
            )
            return GuardrailResult({
                "decision": "blocked",
                "reason": f"Payload size {payload_size} bytes exceeds maximum of {self.MAX_PAYLOAD_SIZE} bytes (1MB)."
            })

        if context is not None:
            context_size = len(json.dumps(context).encode('utf-8'))
            total_size += context_size
            if context_size > self.MAX_CONTEXT_SIZE:
                self.logger.warning(
                    "security_event",
                    extra={
                        "event_type": "context_size_exceeded",
                        "context_size_bytes": context_size,
                        "max_allowed": self.MAX_CONTEXT_SIZE,
                        "exceeded_by_bytes": context_size - self.MAX_CONTEXT_SIZE,
                    }
                )
                return GuardrailResult({
                    "decision": "blocked",
                    "reason": f"Context size {context_size} bytes exceeds maximum of {self.MAX_CONTEXT_SIZE} bytes (64KB)."
                })

        return None

    def _validate_http_payload(self, payload: dict) -> GuardrailResult | None:
        url = payload.get("url", "")
        if not url:
            return GuardrailResult({"decision": "blocked", "reason": "Missing 'url' in payload."})
        parsed = urlparse(url)
        if parsed.scheme not in ("http", "https"):
            return GuardrailResult({"decision": "blocked", "reason": f"Invalid URL scheme: {parsed.scheme}"})
        return None

    def _validate_file_payload(self, payload: dict) -> GuardrailResult | None:
        path = payload.get("relative_path", "")
        if not path:
            return GuardrailResult({"decision": "blocked", "reason": "Missing 'relative_path' in payload."})
        if ".." in path:
            return GuardrailResult({"decision": "blocked", "reason": "Path traversal detected in 'relative_path'."})
        return None

    def evaluate(self, action_name: str, payload: dict) -> GuardrailResult:
        # Check payload size first before any other policy evaluation
        size_check = self._check_payload_size(payload)
        if size_check:
            return size_check

        if action_name in BLOCKED_ACTIONS:
            return GuardrailResult({
                "decision": "blocked",
                "reason": f"Action '{action_name}' is blocked in Phase 10."
            })

        if action_name in ALWAYS_ALLOWED_ACTIONS:
            return GuardrailResult({"decision": "allow"})

        if action_name == "http_request":
            validation_error = self._validate_http_payload(payload)
            if validation_error:
                return validation_error
            url = payload.get("url", "")
            hostname = urlparse(url).hostname or ""
            if hostname not in ALLOWED_HTTP_HOSTS:
                return GuardrailResult({
                    "decision": "blocked",
                    "reason": f"HTTP host '{hostname}' is not allowlisted."
                })
            return GuardrailResult({"decision": "allow"})

        if action_name == "create_file":
            validation_error = self._validate_file_payload(payload)
            if validation_error:
                return validation_error
            relative_path = payload.get("relative_path", "")
            if not any(relative_path.startswith(prefix) for prefix in SAFE_WRITE_PREFIXES):
                return GuardrailResult({
                    "decision": "approval_required",
                    "reason": f"Writing to '{relative_path}' requires approval."
                })
            if action_name in APPROVAL_REQUIRED_ACTIONS:
                return GuardrailResult({"decision": "allow"})
            return GuardrailResult({"decision": "allow"})

        return GuardrailResult({
            "decision": "blocked",
            "reason": f"Unknown or unapproved action '{action_name}'."
        })

    def evaluate_execution(self, request_type: str, payload: dict) -> GuardrailResult:
        # Check payload size first before any other policy evaluation
        size_check = self._check_payload_size(payload)
        if size_check:
            return size_check

        if request_type in ALWAYS_ALLOWED_EXECUTION_TYPES:
            return GuardrailResult({"decision": "allow"})

        if request_type in APPROVAL_REQUIRED_EXECUTION_TYPES:
            return GuardrailResult({
                "decision": "approval_required",
                "reason": f"Execution type '{request_type}' requires approval."
            })

        return GuardrailResult({
            "decision": "blocked",
            "reason": f"Execution type '{request_type}' is not allowed."
        })

    def evaluate_github_execution(self, request_type: str, payload: dict) -> GuardrailResult:
        # Check payload size first before any other policy evaluation
        size_check = self._check_payload_size(payload)
        if size_check:
            return size_check

        if request_type in ALWAYS_ALLOWED_GITHUB_TYPES:
            return GuardrailResult({"decision": "allow"})

        if request_type in APPROVAL_REQUIRED_GITHUB_TYPES:
            return GuardrailResult({
                "decision": "approval_required",
                "reason": f"GitHub request type '{request_type}' requires approval."
            })

        return GuardrailResult({
            "decision": "blocked",
            "reason": f"GitHub request type '{request_type}' is not allowed."
        })

    def evaluate_github_mutation(self, request_type: str, payload: dict) -> GuardrailResult:
        # Check payload size first before any other policy evaluation
        size_check = self._check_payload_size(payload)
        if size_check:
            return size_check

        if request_type in BLOCKED_GITHUB_MUTATION_TYPES:
            return GuardrailResult({
                "decision": "blocked",
                "reason": f"GitHub mutation '{request_type}' remains blocked by policy."
            })

        if request_type in APPROVAL_REQUIRED_GITHUB_MUTATION_TYPES:
            return GuardrailResult({
                "decision": "approval_required",
                "reason": f"GitHub mutation '{request_type}' requires approval."
            })

        return GuardrailResult({
            "decision": "blocked",
            "reason": f"GitHub mutation '{request_type}' is not allowed."
        })

    def evaluate_ops(self, request_type: str, payload: dict) -> GuardrailResult:
        # Check payload size first before any other policy evaluation
        size_check = self._check_payload_size(payload)
        if size_check:
            return size_check

        if request_type in ALWAYS_ALLOWED_OPS_TYPES:
            return GuardrailResult({"decision": "allow"})

        if request_type in APPROVAL_REQUIRED_OPS_TYPES:
            return GuardrailResult({
                "decision": "approval_required",
                "reason": f"Ops request '{request_type}' requires approval."
            })

        return GuardrailResult({
            "decision": "blocked",
            "reason": f"Ops request '{request_type}' is not allowed."
        })

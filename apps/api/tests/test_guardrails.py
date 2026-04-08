from app.guardrails.service import GuardrailService


def test_blocked_action():
    svc = GuardrailService()
    result = svc.evaluate("delete_file", {})
    assert result["decision"] == "blocked"


def test_allowed_action():
    svc = GuardrailService()
    result = svc.evaluate("read_file", {})
    assert result["decision"] == "allow"


def test_http_allowed_host():
    svc = GuardrailService()
    result = svc.evaluate("http_request", {"url": "https://httpbin.org/get"})
    assert result["decision"] == "allow"


def test_http_blocked_host():
    svc = GuardrailService()
    result = svc.evaluate("http_request", {"url": "https://evil.com"})
    assert result["decision"] == "blocked"


def test_create_file_safe_prefix():
    svc = GuardrailService()
    result = svc.evaluate("create_file", {"relative_path": "example/test.txt"})
    assert result["decision"] == "allow"


def test_create_file_unsafe_prefix():
    svc = GuardrailService()
    result = svc.evaluate("create_file", {"relative_path": "restricted/test.txt"})
    assert result["decision"] == "approval_required"


def test_unknown_action_blocked():
    svc = GuardrailService()
    result = svc.evaluate("drop_database", {})
    assert result["decision"] == "blocked"


def test_ops_maintenance_allowed():
    svc = GuardrailService()
    result = svc.evaluate_ops("maintenance_check", {})
    assert result["decision"] == "allow"


def test_ops_deployment_approval():
    svc = GuardrailService()
    result = svc.evaluate_ops("deployment_request", {})
    assert result["decision"] == "approval_required"


def test_github_mutation_merge_blocked():
    svc = GuardrailService()
    result = svc.evaluate_github_mutation("merge_request", {})
    assert result["decision"] == "blocked"


def test_github_mutation_create_branch_approval():
    svc = GuardrailService()
    result = svc.evaluate_github_mutation("create_branch", {})
    assert result["decision"] == "approval_required"

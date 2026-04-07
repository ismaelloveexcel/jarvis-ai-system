class ExecutionError(Exception):
    pass


class ExecutionProvider:
    def run(self, request_type: str, title: str, objective: str, context: dict) -> dict:
        raise NotImplementedError

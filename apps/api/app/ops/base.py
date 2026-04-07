class OpsExecutionError(Exception):
    pass


class OpsProvider:
    def run(self, request_type: str, title: str, environment: str, context: dict) -> dict:
        raise NotImplementedError

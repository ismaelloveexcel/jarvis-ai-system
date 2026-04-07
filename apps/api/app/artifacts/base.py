class ArtifactGenerationError(Exception):
    pass


class ArtifactProvider:
    def generate(self, request_type: str, title: str, content: str, context: dict, output_dir: str) -> dict:
        raise NotImplementedError

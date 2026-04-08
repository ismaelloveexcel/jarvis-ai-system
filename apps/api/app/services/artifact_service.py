from pathlib import Path
from sqlalchemy.orm import Session

from app.artifacts.providers.local_provider import LocalArtifactProvider
from app.models.task_artifact import TaskArtifact


class ArtifactService:
    def __init__(self, db: Session):
        self.db = db
        self.provider = LocalArtifactProvider()
        self.base_dir = Path("workspace/artifacts")

    def capabilities(self) -> dict:
        return {
            "supported_request_types": [
                "generate_patch_artifact",
                "generate_diff_preview",
                "generate_change_bundle",
                "attach_artifact_to_task",
            ]
        }

    def generate_artifact(self, task_id: int, request_type: str, title: str, content: str, context: dict) -> TaskArtifact:
        output_dir = self.base_dir / f"task_{task_id}"
        result = self.provider.generate(
            request_type=request_type,
            title=title,
            content=content,
            context=context,
            output_dir=str(output_dir),
        )

        artifact = TaskArtifact(
            task_id=task_id,
            artifact_type=result["artifact_type"],
            title=result["title"],
            file_path=result["file_path"],
            metadata_json=result["metadata_json"],
        )
        self.db.add(artifact)
        self.db.commit()
        self.db.refresh(artifact)
        return artifact

    def list_task_artifacts(self, task_id: int, limit: int = 50, offset: int = 0) -> list[TaskArtifact]:
        return self.db.query(TaskArtifact).filter(TaskArtifact.task_id == task_id).order_by(TaskArtifact.id.desc()).offset(offset).limit(limit).all()

    def get_artifact(self, artifact_id: int) -> TaskArtifact | None:
        return self.db.query(TaskArtifact).filter(TaskArtifact.id == artifact_id).first()

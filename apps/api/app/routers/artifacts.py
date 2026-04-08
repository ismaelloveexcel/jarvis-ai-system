from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import PlainTextResponse
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.artifact import (
    ArtifactGenerateRequest,
    ArtifactResponse,
    ArtifactCapabilityResponse,
    TaskArtifactResponse,
)
from app.services.artifact_service import ArtifactService
from app.services.task_service import TaskService
from app.services.audit_service import AuditService
from app.models.task import TaskStatus

router = APIRouter()


@router.get("/capabilities", response_model=ArtifactCapabilityResponse)
def artifact_capabilities(db: Session = Depends(get_db)):
    caps = ArtifactService(db).capabilities()
    return ArtifactCapabilityResponse(**caps)


@router.post("/generate", response_model=ArtifactResponse)
def generate_artifact(payload: ArtifactGenerateRequest, db: Session = Depends(get_db)):
    task_service = TaskService(db)
    artifact_service = ArtifactService(db)
    audit_service = AuditService(db)

    if payload.task_id:
        task = task_service.get_task(payload.task_id)
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")
    else:
        task = task_service.create_task(
            user_id=payload.user_id,
            conversation_id=payload.conversation_id,
            task_type="artifact_generation",
            title=payload.title,
            context_json={"request_type": payload.request_type, "context": payload.context},
        )

    audit_service.log(
        event_type="artifact_requested",
        event_status="received",
        details_json={
            "request_type": payload.request_type,
            "title": payload.title,
            "task_id": task.id,
        },
        task_id=task.id,
    )

    try:
        task_service.update_task_status(task, TaskStatus.ANALYZING, current_step="analyzing artifact request")
        task_service.update_task_status(task, TaskStatus.EXECUTING, current_step="generating artifact")

        artifact = artifact_service.generate_artifact(
            task_id=task.id,
            request_type=payload.request_type,
            title=payload.title,
            content=payload.content,
            context=payload.context,
        )

        updated_result = task.result_json or {}
        updated_result["artifact_id"] = artifact.id
        updated_result["artifact_file_path"] = artifact.file_path
        updated_result["artifact_type"] = artifact.artifact_type

        task_service.update_task_status(
            task,
            TaskStatus.COMPLETED,
            current_step="artifact_generated",
            result_json=updated_result,
        )

        audit_service.log(
            event_type="artifact_generated",
            event_status="completed",
            details_json={
                "artifact_id": artifact.id,
                "artifact_type": artifact.artifact_type,
                "file_path": artifact.file_path,
            },
            task_id=task.id,
        )

        return ArtifactResponse(
            task_id=task.id,
            artifact_id=artifact.id,
            result={
                "status": "success",
                "artifact_type": artifact.artifact_type,
                "file_path": artifact.file_path,
            },
        )

    except Exception as exc:
        task_service.update_task_status(
            task,
            TaskStatus.FAILED,
            current_step="artifact_failed",
            result_json={"error": str(exc)},
        )
        audit_service.log(
            event_type="artifact_failed",
            event_status="failed",
            details_json={"error": str(exc)},
            task_id=task.id,
        )
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/task/{task_id}", response_model=list[TaskArtifactResponse])
def list_task_artifacts(task_id: int, limit: int = 50, offset: int = 0, db: Session = Depends(get_db)):
    artifacts = ArtifactService(db).list_task_artifacts(task_id, limit=limit, offset=offset)
    return [
        TaskArtifactResponse(
            id=a.id,
            task_id=a.task_id,
            artifact_type=a.artifact_type,
            title=a.title,
            file_path=a.file_path,
            metadata_json=a.metadata_json or {},
        )
        for a in artifacts
    ]


@router.get("/file/{artifact_id}")
def get_artifact_file(artifact_id: int, db: Session = Depends(get_db)):
    artifact = ArtifactService(db).get_artifact(artifact_id)
    if not artifact:
        raise HTTPException(status_code=404, detail="Artifact not found")

    path = Path(artifact.file_path)
    if not path.exists():
        raise HTTPException(status_code=404, detail="Artifact file missing")

    return PlainTextResponse(path.read_text(encoding="utf-8"))

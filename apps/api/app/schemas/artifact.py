from pydantic import BaseModel, Field
from typing import Any, Literal


class ArtifactGenerateRequest(BaseModel):
    user_id: int = Field(default=1, ge=1)
    conversation_id: int | None = None
    task_id: int | None = None
    request_type: Literal["generate_patch_artifact", "generate_diff_preview", "generate_change_bundle", "attach_artifact_to_task"]
    title: str = Field(..., min_length=1, max_length=500)
    content: str = ""
    context: dict[str, Any] = {}


class ArtifactResponse(BaseModel):
    task_id: int
    artifact_id: int | None = None
    result: dict[str, Any]


class ArtifactCapabilityResponse(BaseModel):
    supported_request_types: list[str]


class TaskArtifactResponse(BaseModel):
    id: int
    task_id: int
    artifact_type: str
    title: str
    file_path: str
    metadata_json: dict

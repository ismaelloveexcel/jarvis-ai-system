from pydantic import BaseModel, Field, field_validator
from typing import Any, Literal
import json


class ArtifactGenerateRequest(BaseModel):
    user_id: int = Field(default=1, ge=1)
    conversation_id: int | None = None
    task_id: int | None = None
    request_type: Literal["generate_patch_artifact", "generate_diff_preview", "generate_change_bundle", "attach_artifact_to_task"]
    title: str = Field(..., min_length=1, max_length=512)
    content: str = ""
    context: dict[str, Any] = {}

    @field_validator('context')
    def validate_context_size(cls, v):
        """Validate context JSON size does not exceed 64KB"""
        if not v:
            return v
        context_json = json.dumps(v)
        if len(context_json.encode('utf-8')) > 65536:  # 64KB
            raise ValueError('context JSON size exceeds maximum of 64KB')
        return v


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

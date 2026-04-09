from pydantic import BaseModel, Field, field_validator
from typing import Any
import json


class ActionRequest(BaseModel):
    user_id: int = Field(default=1, ge=1)
    conversation_id: int | None = None
    action_name: str = Field(..., min_length=1, max_length=255)
    payload: dict[str, Any]

    @field_validator('payload')
    def validate_payload_size(cls, v):
        """Validate total payload JSON size does not exceed 1MB"""
        if not v:
            return v
        payload_json = json.dumps(v)
        payload_size = len(payload_json.encode('utf-8'))
        if payload_size > 1_048_576:  # 1MB
            raise ValueError(f'payload size {payload_size} bytes exceeds maximum of 1MB')
        return v


class ActionResponse(BaseModel):
    task_id: int | None = None
    action_name: str
    result: dict[str, Any]

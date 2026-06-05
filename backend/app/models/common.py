"""Pydantic v2 models for API request/response."""
from __future__ import annotations

from datetime import datetime
from typing import Annotated, Any

from bson import ObjectId
from pydantic import BeforeValidator, Field

# Validator that converts ObjectId -> str when reading from MongoDB
def _validate_object_id(v: Any) -> str:
    if isinstance(v, ObjectId):
        return str(v)
    if isinstance(v, str):
        return v
    raise ValueError(f"Invalid ObjectId: {v!r}")


PyObjectId = Annotated[str, BeforeValidator(_validate_object_id)]


def utc_now() -> datetime:
    from datetime import timezone
    return datetime.now(timezone.utc)

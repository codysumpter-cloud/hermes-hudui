"""Model-info endpoint."""

from fastapi import APIRouter

from backend.collectors.model_info import collect_model_info
from .serialize import to_dict

router = APIRouter()


@router.get("/model-info")
async def get_model_info():
    return to_dict(collect_model_info())

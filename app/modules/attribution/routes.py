from fastapi import APIRouter

from app.pipeline import sample_stage

router = APIRouter(prefix='/api/attribution', tags=['原因归属'])


@router.get('/{sample}', summary='原因归属')
def attribution(sample: str):
    return sample_stage(sample, 'attribution')

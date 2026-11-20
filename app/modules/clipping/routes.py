from fastapi import APIRouter

from app.pipeline import sample_stage

router = APIRouter(prefix='/api/clipping', tags=['时段裁切'])


@router.get('/{sample}', summary='时段裁切')
def clipping(sample: str):
    return sample_stage(sample, 'clipping')

from fastapi import APIRouter

from app.pipeline import sample_stage

router = APIRouter(prefix='/api/reconcile', tags=['可用率核对'])


@router.get('/{sample}', summary='可用率核对')
def reconcile(sample: str):
    return sample_stage(sample, 'reconcile')

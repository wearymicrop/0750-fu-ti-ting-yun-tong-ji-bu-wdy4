from fastapi import APIRouter

from app.pipeline import sample_stage

router = APIRouter(prefix='/api/events', tags=['故障事件'])


@router.get('/{sample}', summary='故障事件')
def events(sample: str):
    return sample_stage(sample, 'events')

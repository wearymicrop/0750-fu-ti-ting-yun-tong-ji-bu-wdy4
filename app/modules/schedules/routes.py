from fastapi import APIRouter

from app.pipeline import sample_stage

router = APIRouter(prefix='/api/schedules', tags=['设备班表'])


@router.get('/{sample}', summary='设备班表')
def schedules(sample: str):
    return sample_stage(sample, 'schedules')

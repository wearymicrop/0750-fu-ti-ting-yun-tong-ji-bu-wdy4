from fastapi import APIRouter

from app.pipeline import sample_stage

router = APIRouter(prefix='/api/exemptions', tags=['豁免计入'])


@router.get('/{sample}', summary='豁免计入')
def exemptions(sample: str):
    return sample_stage(sample, 'exemptions')

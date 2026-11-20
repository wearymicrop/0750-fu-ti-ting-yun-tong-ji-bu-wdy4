from fastapi import APIRouter
from fastapi.responses import Response

from app.errors import BusinessError
from app.modules.openings.batch import build_opening, opening_payload
from app.modules.openings.store import fetch_opening, list_openings, save_opening
from app.modules.reports.store import fetch

router = APIRouter(prefix='/api', tags=['开放记录'])


@router.post('/runs/{report_id}/openings', summary='形成开放结论')
def create(report_id: str):
    data, snapshot = fetch(report_id)
    fresh = build_opening(snapshot)
    if fresh['manifest']['result_digest'] != snapshot['manifest']['digest']:
        raise BusinessError('OPENING_MISMATCH', '班报结果与留档摘要不一致，拒绝裁决', 409)
    return save_opening(fresh)


@router.get('/openings', summary='开放批次')
def batches():
    return list_openings()


@router.get('/runs/{report_id}/openings', summary='读取开放记录')
def detail(report_id: str):
    fetch(report_id)
    return fetch_opening(report_id)


@router.get('/runs/{report_id}/openings/export', summary='下载开放记录')
def export(report_id: str):
    data, _ = fetch(report_id)
    batch = fetch_opening(report_id)
    return Response(opening_payload(batch, data), media_type='application/json',
                    headers={'Content-Disposition':
                             f'attachment; filename="lift-opening-{report_id[:12]}.json"'})

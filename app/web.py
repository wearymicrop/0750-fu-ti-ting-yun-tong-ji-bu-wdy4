from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from app.config import ROOT, RULE_VERSION

router = APIRouter(include_in_schema=False)
templates = Jinja2Templates(directory=ROOT / 'app' / 'templates')
SECTIONS = {
    'reconcile': '可用率核对', 'schedules': '设备班表', 'events': '故障事件',
    'clipping': '时段裁切', 'attribution': '原因归属', 'exemptions': '豁免计入', 'runs': '班报归档',
}


@router.get('/', response_class=HTMLResponse)
def index(request: Request):
    return templates.TemplateResponse(request=request, name='base.html', context={
        'sections': SECTIONS, 'version': RULE_VERSION,
    })

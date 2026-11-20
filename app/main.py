from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from app.config import ROOT
from app.errors import BusinessError
from app.modules.attribution.routes import router as attribution
from app.modules.clipping.routes import router as clipping
from app.modules.events.routes import router as events
from app.modules.exemptions.routes import router as exemptions
from app.modules.reconcile.routes import router as reconcile
from app.modules.reports.routes import router as reports
from app.modules.schedules.routes import router as schedules
from app.web import router as web

app = FastAPI(title='扶梯停运统计簿')
app.mount('/static', StaticFiles(directory=ROOT / 'app' / 'static'), name='static')
for router in (schedules, events, clipping, attribution, exemptions, reconcile, reports, web):
    app.include_router(router)


@app.get('/healthz', summary='健康检查')
def health():
    return {'status': 'ok', 'service': 'lift-duties'}


@app.exception_handler(BusinessError)
def business_error(_: Request, error: BusinessError):
    return JSONResponse({'code': error.code, 'message': str(error)}, status_code=error.status)


@app.exception_handler(RequestValidationError)
def invalid_request(_: Request, error: RequestValidationError):
    fields = [list(item['loc']) for item in error.errors()]
    return JSONResponse({'code': 'INVALID_REQUEST', 'message': '请求字段有误', 'fields': fields}, status_code=422)

from pathlib import Path
import ipaddress
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from app.config import settings
from app.database import Base, engine
from app.routers import auth, products, customers, orders

def _loopback(host:str)->bool:
    try:return ipaddress.ip_address(host).is_loopback
    except ValueError:return host.lower()=="localhost"

if settings.lab_vulnerabilities_enabled and not _loopback(settings.host):
    raise RuntimeError("LAB_VULNERABILITIES_ENABLED requires a loopback host")
@asynccontextmanager
async def lifespan(application:FastAPI):
    Base.metadata.create_all(bind=engine)
    yield
app=FastAPI(title=settings.app_name,version="1.0.0",description="A polished local commerce API with customer, product and order workflows.",openapi_tags=[{"name":"Customers","description":"Customer profiles and addresses."},{"name":"Authentication","description":"Signup, login, token lifecycle and password recovery."},{"name":"Orders","description":"Customer-owned orders and fulfillment."},{"name":"Products","description":"Public catalog, search and reviews."}],lifespan=lifespan)
app.include_router(auth.router);app.include_router(customers.router);app.include_router(orders.router);app.include_router(products.router)
if settings.lab_vulnerabilities_enabled:
    from app.lab_fixture import router as lab_router
    app.include_router(lab_router)
static_dir=Path(__file__).resolve().parent.parent/"static"
api_reference_path=Path(__file__).resolve().parent.parent/"API_REFERENCE.md"
app.mount("/static",StaticFiles(directory=static_dir),name="static")
@app.get("/",include_in_schema=False)
def home():
    return FileResponse(static_dir/"index.html")
@app.get("/api-reference.md",include_in_schema=False)
def api_reference():
    return FileResponse(api_reference_path,media_type="text/markdown")
@app.exception_handler(Exception)
async def generic_error_handler(request:Request,exc:Exception):
    return JSONResponse(status_code=500,content={"detail":"Internal server error"})

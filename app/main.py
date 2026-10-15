from pathlib import Path
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from app.database import init_db
from app.routers import auth, products, customers, orders
from app.logging_middleware import ApiLoggingMiddleware

@asynccontextmanager
async def lifespan(application: FastAPI):
    init_db()
    yield

app = FastAPI(title="Atelier Commerce API", version="1.0.0", description="A commerce API covering authentication, product catalog, and order management.", openapi_tags=[{"name": "Authentication", "description": "Login and token management."}, {"name": "Products", "description": "Public product catalog."}, {"name": "Orders", "description": "Place and manage orders."}], lifespan=lifespan)
app.add_middleware(ApiLoggingMiddleware)
app.include_router(auth.router)
app.include_router(products.router)
app.include_router(customers.router)
app.include_router(orders.router)
static_dir = Path(__file__).resolve().parent.parent / "static"
api_reference_path = Path(__file__).resolve().parent.parent / "API_REFERENCE.md"
app.mount("/static", StaticFiles(directory=static_dir), name="static")

@app.get("/", include_in_schema=False)
def home():
    return FileResponse(static_dir / "index.html")

@app.get("/api-reference.md", include_in_schema=False)
def api_reference():
    return FileResponse(api_reference_path, media_type="text/markdown")

@app.exception_handler(Exception)
async def generic_error_handler(request: Request, exc: Exception):
    return JSONResponse(status_code=500, content={"detail": "Internal server error"})


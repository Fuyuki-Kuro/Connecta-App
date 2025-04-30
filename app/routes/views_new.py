from fastapi import APIRouter, Request, Form, Depends, HTTPException, UploadFile, File
from fastapi.responses import HTMLResponse, RedirectResponse, StreamingResponse
from fastapi.templating import Jinja2Templates
from database import (
    MongoDBConnection,
    UserService,
    ServiceManager,
    PasswordHasher
)
from auth import create_token, verify_token, get_logged_user
from datetime import datetime
from typing import Optional
from io import BytesIO
import gridfs
from bson import ObjectId

# -------------------------
# Jinja2 and Helpers
# -------------------------

templates = Jinja2Templates(directory="app/templates")

# Custom filter to format dates in templates
def datetimeformat(value, format_str: str = "%d/%m/%Y"):  # noqa: A002
    return value.strftime(format_str)

templates.env.filters["datetimeformat"] = datetimeformat

# Helper to build active menu items by user type
def menu_active(user_type: str) -> dict:
    base = {
        "dashboard": True,
        "projetos": True,
        "contrato": True,
        "tickets": True,
        # default false for others
        "calendar": False,
        "equipe": False,
        "pagamentos": False,
    }
    if user_type == "Admin":
        base.update({k: True for k in base})
    elif user_type == "funcionario":
        base.update({"calendar": True, "pagamentos": True})
    # clientes: keep only defaults
    return base

# -------------------------
# Database & GridFS setup
# -------------------------

db_conn = MongoDBConnection()
db = UserService(db_conn=db_conn)
svc = ServiceManager(db_conn=db_conn)
fs = gridfs.GridFS(db_conn.db)  # Use the actual Database instance

# Create API router
router = APIRouter()

# -------------------------
# File Upload & Download
# -------------------------

@router.post("/upload")
async def upload_file(
    request: Request,
    file: UploadFile = File(...)
):
    """
    Upload a file to GridFS and return its ID.
    """
    data = await file.read()
    file_id = fs.put(data, filename=file.filename)
    return {"filename": file.filename, "file_id": str(file_id)}

@router.get("/download/{file_id}")
async def download_file(file_id: str):
    """
    Download a file from GridFS by its ID.
    """
    grid_out = fs.get(ObjectId(file_id))
    stream = BytesIO(grid_out.read())
    return StreamingResponse(
        stream,
        media_type="application/octet-stream",
        headers={
            "Content-Disposition": f"attachment; filename={grid_out.filename}"
        }
    )

@router.get("/image/{file_id}")
async def get_image(file_id: str):
    """
    Serve an image stored in GridFS by its ID.
    """
    grid_out = fs.get(ObjectId(file_id))
    stream = BytesIO(grid_out.read())
    return StreamingResponse(stream, media_type="image/jpeg")

# -------------------------
# Authentication Routes
# -------------------------

@router.get("/", response_class=HTMLResponse)
async def login_get(request: Request):
    """Render the login page or redirect if already logged in."""
    token = request.cookies.get("access_token")
    if token and verify_token(token):
        return RedirectResponse(url="/dashboard", status_code=302)
    return templates.TemplateResponse("login.html", {"request": request})

@router.post("/", response_class=HTMLResponse)
async def login_post(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    manter_conectado: Optional[str] = Form(default=None)
):
    """
    Process login form, set JWT cookie on success.
    """
    user_doc = db.find_user(username)
    if not user_doc or not PasswordHasher.check_password(
        password, user_doc["user"]["senha"]
    ):
        return templates.TemplateResponse(
            "login.html",
            {"request": request, "error": "Usuário ou senha incorretos"}
        )

    token = create_token({"sub": str(user_doc["_id"])})
    response = RedirectResponse(url="/dashboard", status_code=302)
    max_age = (60 * 60 * 24 * 30) if manter_conectado else 60
    response.set_cookie(
        key="access_token",
        value=token,
        httponly=True,
        max_age=max_age,
        samesite="lax",
        secure=False
    )
    return response

# -------------------------
# Dashboard Route
# -------------------------

@router.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request):
    """Render the user dashboard, requires valid JWT cookie."""
    token = request.cookies.get("access_token")
    if not token or not verify_token(token):
        return RedirectResponse(url="/", status_code=302)

    user_id = verify_token(token)
    user_data = db.find_user(user_id)["user"]
    menu = menu_active(user_data["tipo"])

    # Compute dashboard stats...
    ctx = {
        "request": request,
        "user": {
            "name": user_data["nome"],
            "type": user_data["tipo"],
            "role": user_data["cargo"]
        },
        "menu": menu,
        # add other context values here
    }
    return templates.TemplateResponse("dashboard.html", ctx)

# -------------------------
# Services Routes
# -------------------------

@router.get("/services", response_class=HTMLResponse)
async def list_services(
    request: Request,
    user: dict = Depends(get_logged_user)
):
    """List all services with actions based on user role."""

    token = request.cookies.get("access_token")
    if not token or not verify_token(token):
        return RedirectResponse(url="/", status_code=302)

    user_id = verify_token(token)
    user_data = user_data = db.find_user(user_id)["user"]
    user_type = user_data["tipo"]
    actions = {
        "add": user_type == "Admin",
        "edit": user_type == "Admin",
        "delete": user_type == "Admin",
        "view": user_type in ["Admin", "funcionario"],
        "accept": user_type == "funcionario",
        "request_service": user_type == "cliente"
    }
    services = list(svc.collection.find())
    print("Serviços teste meu ovodd")
    return templates.TemplateResponse(
        "services.html",
        {"request": request, "services": services, "actions": actions, "menu": menu_active(user_type)}
    )

@router.get("/services/{service_id}", response_class=HTMLResponse)
async def view_service(
    request: Request,
    service_id: str,
    user: dict = Depends(get_logged_user)
):
    
    token = request.cookies.get("access_token")
    if not token or not verify_token(token):
        return RedirectResponse(url="/", status_code=302)

    user_id = verify_token(token)
    user_data = user_data = db.find_user(user_id)["user"]

    """View details of a single service."""
    service_doc = svc.get_service(service_id)
    if not service_doc["data"]:
        raise HTTPException(status_code=404, detail="Serviço não encontrado")
    return templates.TemplateResponse(
        "view_service.html",
        {"request": request, "service": service_doc["data"], "menu": menu_active(user_data["tipo"]), "user": user}
    )

@router.get("/services/{service_id}/accept")
async def accept_service(
    request: Request,
    service_id: str,
    user: dict = Depends(get_logged_user)
):
   # 1) Decodifica o cookie
    token = request.cookies.get("access_token")
    user_id = verify_token(token)
    if not user_id:
        return RedirectResponse(url="/", status_code=302)

    # 2) Atualiza o serviço no MongoDB
    # Como o documento de serviço está dentro de {"servico": {..., "status": ...}}, usamos operador $set aninhado
    svc_update = svc.update_service(
        service_id,
        {"servico.status": "aceito"}
    )
    if svc_update["status_code"] != 200:
        raise HTTPException(status_code=500, detail="Erro ao atualizar status do serviço")

    # 3) Adiciona esse serviço no services_info do usuário
    user_update = db.add_service_info(user_id, service_id)
    if user_update["status_code"] != 200:
        raise HTTPException(status_code=500, detail="Erro ao registrar serviço para o usuário")

    # 4) Redireciona de volta para a lista de serviços ou dashboard
    return RedirectResponse(url="/services", status_code=302)

@router.get("/logout")
async def logout():
    """Clear auth cookie and redirect to login."""
    response = RedirectResponse(url="/", status_code=302)
    response.delete_cookie("access_token")
    return response

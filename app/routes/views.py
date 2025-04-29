from fastapi import APIRouter, Request, Form, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from db import Database
from auth import create_token, verify_token, get_logged_user
from datetime import datetime

from bson import ObjectId

def to_dict(obj):
    """Recursivamente converte objetos aninhados (como ObjectId) em strings e garante que o resultado seja um dicionário serializável."""
    if isinstance(obj, dict):
        return {k: to_dict(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [to_dict(v) for v in obj]
    elif isinstance(obj, ObjectId):
        return str(obj)
    return obj

def define_menu(user_type):    
     # Defina o menu conforme o tipo
    if user_type == "Admin":
        menu = {
            "dashboard": True,
            "calendar": True,
            "equipe": True,
            "contratos": True,
            "projetos": True,
            "pagamentos": True,
            "tickets": True
        }
        return menu
    
    elif user_type == "funcionario":
        menu = {
            "dashboard": True,
            "calendar": True,
            "equipe": False,
            "projetos": True,
            "pagamentos": True,
            "tickets": True
        }
        return menu
    
    else:  # cliente
        menu = {
            "dashboard": True,
            "calendar": False,
            "equipe": False,
            "projetos": True,
            "pagamentos": False,
            "tickets": False
        }
        return menu


templates = Jinja2Templates(directory="app/templates")
router = APIRouter()
db = Database()

projects = []
postagens = []
ticket = []

def datetimeformat(value, format="short"):
    if not value:
        return ""
    if isinstance(value, str):
        try:
            value = datetime.fromisoformat(value)
        except ValueError:
            return value
    if format == "short":
        return value.strftime("%d/%m/%Y")
    elif format == "time":
        return value.strftime("%H:%M")
    elif format == "full":
        return value.strftime("%d/%m/%Y %H:%M")
    else:
        return value.strftime(format)

templates.env.filters["datetimeformat"] = datetimeformat

# Página de login
@router.get("/", response_class=HTMLResponse)
async def login(request: Request):
    token = request.cookies.get("access_token")
    if token and verify_token(token):
        return RedirectResponse(url="/dashboard", status_code=302)

    return templates.TemplateResponse("login.html", {
        "request": request,
        "error": None
    })

# Autenticação
@router.post("/login")
async def post_login(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    manter_conectado: str = Form(default=None)
):
    user = db.get_users(username)

    if not user or not db.verificar_senha(password, user["senha"]):
        return templates.TemplateResponse("login.html", {
            "request": request,
            "error": "Usuário ou senha incorretos"
        })

    print(f"Manter conectado: {manter_conectado}")

    token = create_token({"sub": str(user["_id"])})
    response = RedirectResponse(url="/dashboard", status_code=302)

    max_age = 60 * 60 * 24 * 30 if manter_conectado == 'true' else 600

    response.set_cookie(
        key="access_token",
        value=token,
        httponly=True,
        max_age=max_age,
        samesite="lax"
    )
    return response

# Dashboard
@router.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request, user=Depends(get_logged_user)):
    projetos_ativos = sum(1 for p in projects if p["status"] == "em andamento")
    total_postagens = len([p for p in postagens if p["status"] != "cancelada"])
    postagens_previstas = 16
    percentual_postagens = round((total_postagens / postagens_previstas) * 100) if postagens_previstas else 0

    faturamento_atual = 5200
    meta_faturamento = 8000
    percentual_faturamento = round((faturamento_atual / meta_faturamento) * 100) if meta_faturamento else 0

    tickets_pendentes = len([t for t in ticket if t["status"] == "pendente"])

    hoje = datetime.now()
    proximas_entregas = []
    for projeto in projects:
        for entrega in projeto["entregas"]:
            data_entrega = datetime.fromisoformat(entrega["data"])
            if data_entrega >= hoje:
                proximas_entregas.append({
                    "data": data_entrega,
                    "descricao": entrega["descricao"]
                })
    proximas_entregas.sort(key=lambda x: x["data"])
    
    user_info = request.cookies.get("access_token")
    if user_info:
        user_info = verify_token(user_info)
        user_info = db.get_user_by_id(user_info)

    user_safe = {
        "name": user_info["nome"],
        "type": user_info["tipo"],
        "role": user_info["cargo"]   
    }

    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "user": user_safe,
        "menu": define_menu(user_safe["type"]),
        "projects_count": projetos_ativos,
        "postagens_count": total_postagens,
        "postagens_percent": percentual_postagens,
        "faturamento_valor": f"R${faturamento_atual:,.0f}".replace(",", "."),
        "faturamento_percent": percentual_faturamento,
        "tickets_pendentes": tickets_pendentes,
        "proximas_entregas": proximas_entregas,
    }

# Calendário
@router.get("/calendario", response_class=HTMLResponse)
async def calendario(request: Request):
    return templates.TemplateResponse("calendario.html", {"request": request, "page": "calendario"})

# Serviços
@router.get("/servicos", response_class=HTMLResponse)
async def servicos(request: Request, user=Depends(get_logged_user)):
    user_info = request.cookies.get("access_token")
    if user_info:
        user_info = verify_token(user_info)
        user_info = db.get_user_by_id(user_info)

    user_safe = {
        "name": user_info["nome"],
        "type": user_info["tipo"],
        "role": user_info["cargo"]   
    }

    services = db.get_services()

    return templates.TemplateResponse("service.html", {
        "request": request,
        "user": user_safe,
        "menu": define_menu(user_safe["type"]),
        "services": services,
    })

# Adicionar serviço
@router.get("/servicos/adicionar")
async def add_service(request: Request, user= Depends(get_logged_user)):
    return templates.TemplateResponse("add_service.html", {
        "cliente": db.get_clients(),
        "request": request,
        "user": request.cookies.get("access_token"),
        "menu": define_menu(request.cookies.get("access_token"))
    })

@router.post("/servicos/adicionar")
async def add_service(request: Request, user= Depends(get_logged_user)):
    user = request.cookies.get("access_token")
    if user:
        user = db.get_user(user)
        if user["tipo"] != "Admin":
             raise HTTPException(status_code=403, detail="Acesso negado")

    print(data)
    return templates.TemplateResponse("add_service.html", {
        "cliente": db.get_clients(),
        "request": request,
        "user": request.cookies.get("access_token"),
        "menu": define_menu(request.cookies.get("access_token"))
    })

# Logout
@router.get("/logout")
async def logout():
    response = RedirectResponse(url="/", status_code=302)
    response.delete_cookie("access_token")
    return response

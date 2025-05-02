from fastapi import APIRouter, Request, Depends, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi import status


router = APIRouter(tags=["Backend","plugins"])


#implementa a IA de gestão de projetos
@router.post("/plugins/IaProjetos")
async def IaProjetos(request: Request,
cookie:str,
nome: str,
tipo: str,
descricao: str,

):
    
    if not cookie:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token inválido")
    return {"nome": nome, "tipo": tipo, "descricao": descricao, "cookie": cookie}


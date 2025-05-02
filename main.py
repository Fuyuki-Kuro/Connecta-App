from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from app.routes import views_new as views
from app.routes import plugins 

app = FastAPI(title="FastAPI App", version="1.0.0")

# Monta arquivos estáticos (CSS, imagens etc)
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# Inclui rotas de páginas
app.include_router(views.router)
app.include_router(plugins.router)

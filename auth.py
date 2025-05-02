from jose import JWTError, jwt
from datetime import datetime, timedelta, UTC
import os
from fastapi import Request, HTTPException
import re
from dotenv import load_dotenv

load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 120

def verify_cpf(cpf: str) -> bool:
    # Remover caracteres não numéricos
    cpf = re.sub(r'[^0-9]', '', cpf)

    # Verificar o tamanho do CPF
    if len(cpf) != 11:
        return False
    
    # Descarta CPF com todos os dígitos iguais
    if cpf == cpf[0] * 11:
        return False
    
    # Função para calcular o dígito verificador
    def calc_remainder(cpf_parcial: str) -> str:
        initial_length = len(cpf_parcial) + 1
        soma = sum(int(d) * (initial_length - idx) for idx, d in enumerate(cpf_parcial, start=1))
        resto = soma % 11
        return "0" if resto < 2 else str(11 - resto)
    
    # Calcula o primeiro e segundo dígito verificador
    digito_1 = calc_remainder(cpf[:9])
    digito_2 = calc_remainder(cpf[:9] + digito_1)

    # Verifica se os dígitos calculados são iguais aos fornecidos
    return cpf[-2:] == digito_1 + digito_2
    print("teste 4")

def create_token(data: dict):
    to_encode = data.copy()
    expire = datetime.now(UTC) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def verify_token(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload.get("sub")
    except JWTError:
        return None

def get_logged_user(request: Request):
    token = request.cookies.get("access_token")
    if not token:
        raise HTTPException(status_code=401, detail="Token not found")

    user_id = verify_token(token)
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid token")

    return user_id


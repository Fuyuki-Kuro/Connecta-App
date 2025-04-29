from pymongo import MongoClient
from bson import ObjectId
import os
from dotenv import load_dotenv
import bcrypt

load_dotenv()

class Database:
    def __init__(self):
        try:
            self.client = MongoClient(os.getenv("MONGO_URI"))
            self.db = self.client["connecta"]
            self.users_collection = self.db["users"]
            self.service_collection = self.db["services"]
            self.client.admin.command("ping")
            print("✅ Conexão com MongoDB Atlas estabelecida com sucesso.")
        except Exception as e:
            print("❌ Erro na conexão com o MongoDB:", e)

    def hash_password(self, senha):
        return bcrypt.hashpw(senha.encode('utf-8'), bcrypt.gensalt())

    def verificar_senha(self, senha, senha_hash):
        return bcrypt.checkpw(senha.encode('utf-8'), senha_hash)

    def get_users(self, username):
        return self.users_collection.find_one({"username": username})

    def get_user_by_id(self, user_id):
        try:
            return self.users_collection.find_one({"_id": ObjectId(user_id)})
        except Exception as e:
            print("Erro ao buscar usuário por ID:", e)
            return None
    
    def get_clients(self):
        return self.users_collection.find({"tipo": "cliente"})

    def add_user(self, user):
        try:
            user["senha"] = self.hash_password(user["senha"])
            result = self.users_collection.insert_one(user)
            return {"status_code": 200, "message": "Usuário adicionado com sucesso", "id": str(result.inserted_id)}
        except Exception as e:
            return {"status_code": 400, "message": "Erro ao adicionar usuário", "erro": str(e)}

    def get_services(self):
        return self.service_collection.find()

    def add_service(self, service: dict):
        """Adiciona um novo serviço."""
        result = self.services_collection.insert_one(service)
        return str(result.inserted_id)
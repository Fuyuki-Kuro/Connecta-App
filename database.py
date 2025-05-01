import os
import bcrypt
import hashlib
import gridfs
from dotenv import load_dotenv
from pymongo import MongoClient
from bson import ObjectId
from auth import verify_cpf

load_dotenv()

class MongoDBConnection:
    """
    Singleton para conexão com o MongoDB e GridFS.
    """
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            uri = os.getenv("MONGO_URI")
            client = MongoClient(uri, tlsAllowInvalidCertificates=True)
            db = client[os.getenv("MONGO_DB_NAME", "connecta")]
            fs = gridfs.GridFS(db)

            # Testa conexão
            client.admin.command("ping")
            print("✅ MongoDB Atlas conectado.")

            cls._instance = super().__new__(cls)
            cls._instance.client = client
            cls._instance.db = db
            cls._instance.fs = fs
        return cls._instance

class PasswordHasher:
    """
    Encarregado de gerar e verificar hashes de senha.
    """
    @staticmethod
    def hash_password(password: str) -> bytes:
        return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

    @staticmethod
    def check_password(password: str, hashed: bytes) -> bool:
        return bcrypt.checkpw(password.encode('utf-8'), hashed)

class UserService:
    """
    Serviços relacionados ao usuário: cadastro e validação.
    """
    def __init__(self, db_conn: MongoDBConnection):
        self.collection = db_conn.db['users']

    def add_user(self, user: dict) -> dict:

        user_info = user["user"]
        # Checa existência
        if self.collection.find_one({"user.username": user_info["username"]}):
            return {"status_code": 400, "message": "Usuário já existe"}
        if self.collection.find_one({"user.email": user_info["email"]}):
            return {"status_code": 400, "message": "Email já está sendo usado"}
        if not verify_cpf(user_info["cpf"]):
            return {"status_code": 400, "message": "CPF inválido"}
        if self.collection.find_one({"user.cpf": user_info["cpf"]}):
            return {"status_code": 400, "message": "CPF já está sendo usado"}

        # Hash da senha
        user_info["senha"] = PasswordHasher.hash_password(user_info["senha"])
        try:
            result = self.collection.insert_one(user)
            return {"status_code": 200, "message": "Usuário adicionado com sucesso", "id": str(result.inserted_id)}
        except Exception as e:
            return {"status_code": 500, "message": "Erro ao adicionar usuário", "erro": str(e)}

    def find_user(self, identifier: str) -> dict:
        # Busca por ObjectId ou username
        if ObjectId.is_valid(identifier):
            query = {"_id": ObjectId(identifier)}
        else:
            query = {"user.username": identifier}
        return self.collection.find_one(query)
    
    def delete_user(self, identifier: str) -> dict:
        # Busca por ObjectId ou username
        if ObjectId.is_valid(identifier):
            query = {"_id": ObjectId(identifier)}
            result = self.collection.delete_one(query)
            return {"status_code": 200, "message": "Usuário excluído com sucesso", "data": result}
        else:
            query = {"username": identifier}
            return {"status_code": 400, "message": "Usuário não encontrado"}
        
    def add_service_info(self, user_id: str, service_id) -> dict:
        service_data = {
            "service_id": service_id,
            "status": "PENDENTE"
        }

        try:
            result = self.collection.update_one(
                {"_id": ObjectId(user_id)},
                {"$push": {"services_info": service_data}}
            )
            if result.modified_count:
                # muda o status do serviço para aceito
                self.service_manager.update_service(
                    service_id,
                    {"servico.status": "EM ANDAMENTO"}
                )
                return {"status_code": 200, "message": "Serviço adicionado com sucesso"}
            
            return {"status_code": 500, "message": "Falha ao atualizar usuário"}
        except Exception as e:
            return {"status_code": 500, "message": "Erro ao adicionar serviço", "erro": str(e)}
        
class ServiceManager:
    """
    Serviços de criação e consulta de serviços.
    """
    def __init__(self, db_conn: MongoDBConnection):
        self.collection = db_conn.db['services']

    def add_service(self, service: dict) -> dict:
        try:
            result = self.collection.insert_one(service)
            return {"status_code": 200, "message": "Serviço adicionado com sucesso", "id": str(result.inserted_id)}
        except Exception as e:
            return {"status_code": 500, "message": "Erro ao adicionar serviço", "erro": str(e)}

    def get_service(self, id: str) -> dict:
        try:    
            result = self.collection.find_one({"_id": id})
            return {"status_code": 200, "message": "Serviço encontrado com sucesso", "data": result}
        except Exception as e:
            return {"status_code": 500, "message": "Erro ao buscar serviço", "erro": str(e)}
        
    def update_service(self, id: str, data: dict) -> dict:
        try:
            # data pode ser {"servico.status": "aceito"} ou qualquer outro campo aninhado
            result = self.collection.update_one(
                {"_id": id},
                {"$set": data}
            )
            return {"status_code": 200, "message": "Serviço atualizado com sucesso", "data": result}
        except Exception as e:
            return {"status_code": 500, "message": "Erro ao atualizar serviço", "erro": str(e)}

    
    def delete_service(self, id: str) -> dict:
        try:
            result = self.collection.delete_one({"_id": ObjectId(id)})
            return {"status_code": 200, "message": "Serviço excluído com sucesso", "data": result}
        except Exception as e:
            return {"status_code": 500, "message": "Erro ao excluir serviço", "erro": str(e)}

class TicketManager:
    """
    Serviços de criação e consulta de tickets.
    """
    def __init__(self, db_conn: MongoDBConnection):
        self.collection = db_conn.db['tickets']

    def add_ticket(self, ticket: dict) -> dict:
        try:
            result = self.collection.insert_one(ticket)
            return {"status_code": 200, "message": "Ticket adicionado com sucesso", "id": str(result.inserted_id)}
        except Exception as e:
            return {"status_code": 500, "message": "Erro ao adicionar ticket", "erro": str(e)}

    def update_ticket(self, id: str, data: dict) -> dict:
        try:
            result = self.collection.update_one({"_id": ObjectId(id)}, {"$set": data})
            return {"status_code": 200, "message": "Ticket atualizado com sucesso", "data": result}
        except Exception as e:
            return {"status_code": 500, "message": "Erro ao atualizar ticket", "erro": str(e)}
        
    def delete_ticket(self, id: str) -> dict:
        try:
            result = self.collection.delete_one({"_id": ObjectId(id)})
            return {"status_code": 200, "message": "Ticket excluído com sucesso", "data": result}
        except Exception as e:
            return {"status_code": 500, "message": "Erro ao excluir ticket", "erro": str(e)}
    
    def get_ticket(self, id: str) -> dict:
        try:
            result = self.collection.find_one({"_id": ObjectId(id)})
            return {"status_code": 200, "message": "Ticket encontrado com sucesso", "data": result}
        except Exception as e:
            return {"status_code": 500, "message": "Erro ao buscar ticket", "erro": str(e)}

class ContractManager:
    """
    Serviços de criação e gerenciamento de contratos.
    """
    def __init__(self, db_conn: MongoDBConnection):
        self.users = db_conn.db['users']
        self.fs = db_conn.fs

    def add_contract(self, user_identifier: str, contract_data: dict, file_bytes: bytes, filename: str) -> dict:
        # Localiza usuário
        user = UserService(MongoDBConnection()).find_user(user_identifier)
        if not user:
            return {"status_code": 404, "message": "Usuário não encontrado"}

        contract_id = ObjectId()
        hash_contract = hashlib.sha256(file_bytes).hexdigest()
        file_id = self.fs.put(file_bytes, filename=filename, metadata={"hash_contract": hash_contract})

        new_contract = {
            "_id": contract_id,
            "nome": contract_data["nome"],
            "valor": contract_data["valor"],
            "data_de_vencimento": contract_data["data_de_vencimento"],
            "status": "ativo",
            "file_id": file_id,
            "hash_contract": hash_contract
        }
        try:
            result = self.users.update_one(
                {"_id": user["_id"]},
                {"$push": {"contracts_info": new_contract}}
            )
            if result.modified_count:
                return {"status_code": 200, "message": "Contrato adicionado com sucesso", "contract_id": str(contract_id)}
            return {"status_code": 500, "message": "Falha ao atualizar usuário"}
        except Exception as e:
            return {"status_code": 500, "message": "Erro ao adicionar contrato", "erro": str(e)}

    # Podem ser chamados conforme a necessidade:
    # user_service.add_user({...})
    # service_mgr.add_service({...})
    # ticket_mgr.add_ticket({...})
    # contract_mgr.add_contract(user_id, contrato, bytes_data, 'contrato.pdf')

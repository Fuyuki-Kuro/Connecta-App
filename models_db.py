from bson import ObjectId

from database import UserService, MongoDBConnection, ServiceManager, TicketManager, ContractManager
import secrets

postagens = [
  {
    "_id": "pst001",
    "titulo": "Promoção Dia das Mães",
    "projeto_id": "prj001",
    "data_agendada": "2025-04-20T10:00:00",
    "status": "agendada"
  },
  {
    "_id": "pst002",
    "titulo": "Reels Teaser",
    "projeto_id": "prj001",
    "data_agendada": "2025-04-21T17:00:00",
    "status": "agendada"
  }
]


user_info = {
    "_id": ObjectId(),
    "user": {
        "nome": "Leonard Henrique",
        "username": "leonard_connecta",
        "cpf": "12345678900",
        "rg": "12345678-9",
        "email": "leonard@xpto.com",
        "tipo": "funcionario",
        "cargo": "Designer",
        "senha": "777-Rroot"
    },
    "tickets": [
        {
            "titulo": "Alterar texto da arte",
            "mensagem": "Preciso que troquem o texto do post do dia 20.",
            "status": "pendente",
            "data_criacao": "2025-04-16T14:00:00"
        }
    ],
    "contracts_info": [
        {
            "nome": "Contrato 1",
            "hash_contract": "123456789",
            "valor": 1000,
            "data_de_vencimento": "2025-04-20T14:00:00",
            "status": "ativo"
        }
    ],
    "services_info": [
        {
            "nome": "Projeto 1",
            "valor": 1000,
            "status": "em andamento"
        }
    ],
    "status": "ativo",
    }


ticket_info = {
    "_id": "tkt001",
    "user_info": {
        "id": "3829018309123",
        "nome": "Flávio",
        "email": "flavio@xpto.com",
    },
    "ticket": {
        "titulo": "Alterar texto da arte",
        "mensagem": "Preciso que troquem o texto do post do dia 20.",
        "status": "pendente",
        "data_criacao": "2025-04-16T14:00:00"
    }
}

services = {
    "_id": "srv001",
    "cliente_info": {
        "id": "usr005",
        "nome": "Empresa XPTO",
        "email": "contato@xpto.com",
    },
    "servico": {
        "nome": "Agendamento",
        "tipo": "agendamento",
        "descricao": "Criação de agendamentos para projetos",
        "data_de_entrega": "2025-04-20",
        "media": [
            {"imagem": "imagem1.jpg", "descricao": "Imagem 1"},
            {"imagem": "imagem2.jpg", "descricao": "Imagem 2"},
            {"imagem": "imagem3.jpg", "descricao": "Imagem 3"}
        ],
        "status": "ativo"
    }
}

contracts = {
    "_id": "ctr001",
    "user_info": {
        "id": "usr005",
        "nome": "Empresa XPTO",
        "cpf": "12345678901",
        "rg": "12345678-9",
        "email": "contato@xpto.com",
        "endereco": "Rua do Cliente, 123",
        "cidade": "São Paulo",
        "estado": "SP",
        "cep": "01234567",
        "telefone": "123456789",
        "celular": "123456789",
        "tipo": "cliente",
        "cargo": "gerente",
    },
    "contrato": {
        "nome": "Contrato 1",
        "valor": 1000,
        "data_de_vencimento": "2025-04-20T14:00:00",
        "status": "ativo"
    }
    }



user_info = {
    "_id": ObjectId(),
    "user": {
        "nome": "Leonard Henrique",
        "username": "leonard_connecta",
        "cpf": "12345678900",
        "rg": "12345678-9",
        "email": "leonard@xpto.com",
        "tipo": "funcionario",
        "cargo": "Designer",
        "senha": "777-Rroot"
    },
    "tickets": [],
    "contracts_info": [],
    "services_info": [],
    "status": "PENDENTE",
    }

services = {
    "_id": "srv" + secrets.token_hex(4),
    "cliente_info": {
            "id": "usr004",
            "nome": "Empresa D",
            "email": "contato@empresaD.com",
        },
    "servico": {
        "nome": "Design Gráfico",
        "tipo": "design gráfico",
        "descricao": "Criação de identidade visual e logotipos",
        "data_de_entrega": "2025-05-20",
        "media": [
            {"imagem": "imagem1_950b2c05.jpg", "descricao": "Imagem 1"},
            {"imagem": "imagem2_74e034f4.jpg", "descricao": "Imagem 2"},
            {"imagem": "imagem3_b4ac58e2.jpg", "descricao": "Imagem 3"}
        ],
        "status": "ativo"
    }
}



db = MongoDBConnection()
service = UserService(db_conn=db)
result = service.add_user(user_info)
print(result)


service = ServiceManager(db_conn=db)
result = service.add_service(services)

print(result)
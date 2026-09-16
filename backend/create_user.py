#!/usr/bin/env python3
"""
Cria o usuário admin inicial diretamente no Supabase.

Credenciais vêm do ambiente, nunca do código. A versão anterior deste script
trazia e-mail e senha embutidos, e um arquivo versionado é um arquivo publicado:
qualquer senha escrita aqui vaza no primeiro push e continua no histórico depois
de corrigida.

Uso:
    ADMIN_EMAIL=voce@exemplo.com ADMIN_PASSWORD='...' ADMIN_NAME='Seu Nome' \
        venv/Scripts/python.exe create_user.py
"""

import os
import sys
import uuid

import bcrypt
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

if not SUPABASE_URL or not SUPABASE_SERVICE_ROLE_KEY:
    print("❌ ERRO: SUPABASE_URL ou SUPABASE_SERVICE_ROLE_KEY não definidos no .env")
    sys.exit(1)

email = os.getenv("ADMIN_EMAIL")
password = os.getenv("ADMIN_PASSWORD")
full_name = os.getenv("ADMIN_NAME", "Administrador")

# Falha explícita em vez de valor padrão: um padrão aqui viraria a conta admin
# que todo mundo conhece.
faltando = [
    nome
    for nome, valor in (("ADMIN_EMAIL", email), ("ADMIN_PASSWORD", password))
    if not valor
]
if faltando:
    print(f"❌ ERRO: defina {' e '.join(faltando)} no ambiente antes de rodar.")
    print("   Exemplo: ADMIN_EMAIL=voce@exemplo.com ADMIN_PASSWORD='...' python create_user.py")
    sys.exit(1)

if len(password) < 12:
    print("❌ ERRO: use uma senha de pelo menos 12 caracteres.")
    sys.exit(1)

from supabase import Client, create_client

supabase: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)

password_hash = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
user_id = str(uuid.uuid4())

try:
    supabase.table("users").insert(
        {
            "id": user_id,
            "email": email,
            "password_hash": password_hash,
            "full_name": full_name,
            "role": "admin",
        }
    ).execute()

    print("=" * 60)
    print("✅ USUÁRIO CRIADO COM SUCESSO!")
    print("=" * 60)
    print(f"   ID: {user_id}")
    print(f"   Email: {email}")
    print(f"   Nome: {full_name}")
    print("   Role: admin")
    print("=" * 60)

except Exception as e:
    if "duplicate key" in str(e).lower() or "already exists" in str(e).lower():
        print("⚠️  Usuário já existe!")
        print(f"   Email: {email}")
    else:
        print(f"❌ Erro ao criar usuário: {e}")
        sys.exit(1)

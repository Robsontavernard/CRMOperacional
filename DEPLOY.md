# Deploy

Frontend na **Vercel**, backend no **Render**. Suba o backend primeiro: o
frontend precisa da URL dele em tempo de build.

## Por que o backend não é serverless

`backend/main.py` sobe um APScheduler com dois jobs:

| job | quando | o que faz |
|---|---|---|
| `auto_sync_drive_transcriptions` | a cada 5 min | lê as transcrições novas no Google Drive |
| `daily_comercial_alerts` | 7h, America/Sao_Paulo | gera os alertas comerciais |

Os dois exigem processo vivo. Em serverless (Vercel Functions, Lambda) eles
simplesmente não rodam — e não falham: o sistema fica quieto e para de receber
transcrição. Pelo mesmo motivo o Render precisa de plano pago; o free hiberna
depois de 15 minutos sem requisição.

---

## 1. Backend no Render

**New → Blueprint → aponte para este repositório.** O `render.yaml` na raiz traz
build, start, health check e Python 3.11.9 prontos.

O Render vai pedir o valor das variáveis marcadas `sync: false` — elas não estão
versionadas de propósito:

| variável | obrigatória | onde conseguir |
|---|---|---|
| `SUPABASE_URL` | sim | Supabase → Project Settings → API |
| `SUPABASE_SERVICE_ROLE_KEY` | sim | idem (é a chave **service_role**, não a anon) |
| `PIPEDRIVE_API_TOKEN` | sim | Pipedrive → Personal preferences → API |
| `GOOGLE_DRIVE_SERVICE_ACCOUNT_JSON` | sim | **cole o conteúdo do JSON inteiro** |
| `JWT_SECRET` | sim | o Render gera sozinho (`generateValue`) |
| `GEMINI_API_KEY` | não | só o assistente para sem ela |
| `NVIDIA_API_KEY` | não | fallback do assistente |
| `CORS_ORIGINS` | depois | preencher no passo 3 |

`GOOGLE_DRIVE_SERVICE_ACCOUNT_JSON` aceita três formatos — JSON colado, Base64
ou caminho de arquivo (ver `get_drive_service()`). **No Render, cole o JSON**:
não existe arquivo para apontar.

⚠️ `JWT_SECRET` novo **invalida todos os logins existentes**. É o
comportamento certo numa troca de conta, mas avise quem usa: todo mundo vai
precisar entrar de novo.

Não configure `SUPABASE_ANON_KEY`, `PIPEDRIVE_BASE_URL` nem `APP_URL` — estão no
`.env.example` por herança, e nenhuma é lida pelo código.

**Mantenha uma instância só.** Com duas, cada uma sobe o próprio scheduler: a
sincronização roda em dobro e o alerta comercial sai duplicado.

Ao final, anote a URL: `https://crm-operacional-api.onrender.com`.

## 2. Frontend na Vercel

**Add New → Project → importe `Robsontavernard/CRMOperacional`.**

| configuração | valor |
|---|---|
| **Root Directory** | `frontend` |
| Framework Preset | Next.js (detectado sozinho) |
| Build / Install / Output | deixe em branco |
| Node.js Version | 20.x |
| Production Branch | `main` |

**O Root Directory é o item que quebra tudo se estiver errado** — o repositório
tem `frontend/` e `backend/` na raiz, e sem apontar para `frontend` o build
falha com `NEXT_NOT_FOUND`. Ele **não** pode ser definido no `vercel.json`: é
configuração de projeto, só existe no painel. O `frontend/vercel.json` cobre o
resto (framework, `npm ci`), mas só passa a valer depois que o Root Directory
estiver certo.

Variável de ambiente, marcando **Production, Preview e Development**:

```
NEXT_PUBLIC_API_URL = https://crm-operacional-api.onrender.com
```

⚠️ **`NEXT_PUBLIC_*` é embutido no bundle em tempo de build, não lido em
execução.** Mudar o valor no painel não tem efeito nenhum até um **redeploy**.

Ligue **Deployment Protection → Vercel Authentication**: é ferramenta interna
com dado de cliente, e a URL de produção não deveria ficar aberta.

## 3. Fechar o CORS

Com a URL da Vercel em mãos, volte ao Render e defina:

```
CORS_ORIGINS = https://seu-projeto.vercel.app,https://dominio-proprio.com.br
```

Sem essa variável a API aceita requisição de qualquer origem. Continua
funcionando — e escreve um `WARNING` no startup dizendo exatamente isso.

## 4. Conferir

1. `https://<backend>/health` responde
2. O log de startup do Render **não** traz o aviso de `CORS_ORIGINS`
3. Login funciona (senha nova: o `JWT_SECRET` mudou)
4. Após ~5 min, o log mostra a sincronização do Drive rodando

## Banco

O Supabase é o mesmo em qualquer ambiente — não há banco de staging. Num projeto
novo, rode `schema.sql` e `schema_base_clientes.sql`, nessa ordem, no SQL Editor.

## Criar o primeiro usuário

```bash
ADMIN_EMAIL=voce@exemplo.com ADMIN_PASSWORD='...' ADMIN_NAME='Seu Nome' \
    python create_user.py
```

Rode a partir de `backend/`, com `SUPABASE_URL` e `SUPABASE_SERVICE_ROLE_KEY` no
ambiente. A senha precisa de 12 caracteres ou mais.

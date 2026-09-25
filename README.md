# EMGEPRON | Plataforma de Ativos Ambientais — V1

V1 demonstrativa da infraestrutura conceitual.

## O que já funciona

- Tela de login
- Solicitação/cadastro de usuário
- Geração de senha temporária
- Simulação do e-mail com a senha temporária
- Primeiro acesso com troca obrigatória da senha
- Banco SQLite local
- Sessão de usuário
- Dashboard pós-login
- Portfólio inicial de projetos
- Indicadores agregados
- Perfil de usuário
- Logout

## O que ainda NÃO está implementado

- Envio real de e-mail institucional
- 2FA por código real
- Gestão completa de usuários pelo administrador
- Blockchain
- Smart contracts
- Certificação/verificação externa
- Integração com Excel/API
- Banco de dados corporativo
- Controle de acesso granular

Esses itens ficam para as próximas versões.

## Como executar

```bash
python -m venv .venv
```

Windows:

```bash
.venv\Scripts\activate
pip install -r requirements.txt
python app.py
```

Depois abra:

http://127.0.0.1:5000

## Usuário de demonstração

E-mail:
`admin@emgepron.local`

Senha:
`Admin@123`

## Observação de segurança

Esta é uma V1 de protótipo. Antes de qualquer uso institucional, trocar a SECRET_KEY, remover credenciais demonstrativas, usar HTTPS, banco corporativo, gestão de segredos, política de senha, MFA real, logs de auditoria e controles de segurança adequados.

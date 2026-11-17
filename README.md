# Radar Acadêmico

Aplicação educacional em FastAPI para integração e acompanhamento de estagiários em Farmácia Hospitalar.

## O que esta versão contém
- Cadastro de aluno com aprovação manual do preceptor.
- Login com hash Argon2 e sessão assinada.
- Oito módulos introdutórios, elaborados a partir do manual de treinamento disponibilizado.
- Quiz por módulo; nota mínima de 70% marca o módulo como concluído.
- Registro de atividades práticas e validação/rejeição pelo preceptor.
- Certificado imprimível após concluir os oito módulos.
- Backup SQLite pelo painel do preceptor.
- SQLite local ou PostgreSQL via `DATABASE_URL`.

## Rodar localmente no Linux
Requer Python 3.11 ou superior.

```bash
cd radar-academico
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# Edite .env e defina SECRET_KEY e os dados iniciais do preceptor.
set -a; source .env; set +a
uvicorn main:app --reload
```
Acesse http://127.0.0.1:8000/ e confira http://127.0.0.1:8000/health.

## Primeiro preceptor
Defina `INITIAL_PRECEPTOR_CPF` (11 dígitos, sem pontuação), `INITIAL_PRECEPTOR_PASSWORD` (mínimo 12 caracteres) e `INITIAL_PRECEPTOR_NAME` antes da primeira inicialização. O usuário será criado com perfil preceptor. Guarde as credenciais em local seguro e remova-as das variáveis de implantação após o bootstrap, se desejar.

## GitHub
1. Crie um repositório privado inicialmente, especialmente enquanto estiver em validação.
2. Não inclua `.env`, banco de dados, backups, CPF real ou dados de estagiários.
3. No diretório do projeto:

```bash
git init
git add .
git commit -m "Preparar Radar Acadêmico para implantação"
git branch -M main
git remote add origin https://github.com/SEU-USUARIO/radar-academico.git
git push -u origin main
```

## Render
1. Crie um Web Service a partir do repositório GitHub.
2. O arquivo `render.yaml` contém build, start, health check e disco persistente de 1 GB em `/var/data`.
3. Configure `INITIAL_PRECEPTOR_CPF` e `INITIAL_PRECEPTOR_PASSWORD` em Environment. Não use credenciais reais no Git.
4. Para produção com vários usuários, considere PostgreSQL gerenciado e configure `DATABASE_URL`; nesse caso, planeje backup pelo provedor. O backup em rota da aplicação é exclusivo para SQLite.
5. Confirme o plano do Render: disco persistente pode exigir plano pago e não está incluído em todos os planos gratuitos.

## Testes
```bash
pytest -q
```

## Pontos que exigem validação institucional antes do uso real
- Revisão técnica e pedagógica dos oito módulos, quizzes e carga horária pelo responsável.
- Aprovação formal dos critérios de avaliação e modelo de certificado.
- Definição de política de privacidade, retenção e descarte de dados pessoais (LGPD).
- Configuração de HTTPS, segredo forte, política de acesso e backup externo testado.
- O material de oncologia é introdutório; não substitui treinamento prático, protocolos locais ou supervisão.
- Esta versão não importa automaticamente usuários/senhas antigos: os hashes inseguros em texto puro da versão legada não são reaproveitados.

## Segurança e operação
Esta entrega é uma base funcional inicial, não uma homologação de produção. Antes de abrir para uso externo, implemente e teste proteção CSRF nos formulários, política de privacidade/consentimento, limitação de tentativas de login, recuperação de senha, logs sem dados sensíveis e rotina de restauração de backup. O middleware de sessão usa cookie `HttpOnly` por padrão do Starlette e `Secure` em produção; a aplicação exige segredo próprio em produção. Não cadastre dados reais de pacientes nesta plataforma.

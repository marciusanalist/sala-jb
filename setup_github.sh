#!/bin/bash
# Script de publicação — Casa JB Agendamento
set -e

REPO_NAME="casa-jb-agendamento"
DIR="$(cd "$(dirname "$0")" && pwd)"

echo ""
echo "🏛️  Casa JB — Publicar no GitHub"
echo "=================================="
echo ""

cd "$DIR"

# Inicializar git se necessário
if [ ! -d ".git" ]; then
  git init
  echo "✅ Repositório git inicializado"
fi

# Adicionar tudo e commitar
git add .
git diff --cached --quiet || git commit -m "feat: sistema de agendamento Casa JB v1.0"
echo "✅ Commit criado"

# Verificar se gh está instalado
if ! command -v gh &> /dev/null; then
  echo ""
  echo "⚠️  GitHub CLI (gh) não encontrado."
  echo "   Instale em: https://cli.github.com"
  echo "   Depois rode: brew install gh && gh auth login"
  echo ""
  exit 1
fi

# Verificar autenticação
if ! gh auth status &> /dev/null; then
  echo ""
  echo "🔐 Fazendo login no GitHub..."
  gh auth login
fi

# Criar repositório no GitHub e fazer push
echo ""
echo "📤 Criando repositório '$REPO_NAME' no GitHub..."
gh repo create "$REPO_NAME" \
  --public \
  --description "Sistema de agendamento de salas — Casa JB" \
  --source=. \
  --remote=origin \
  --push 2>/dev/null || {
    # Repositório já existe — só faz push
    echo "   (repositório já existe, fazendo push...)"
    git remote set-url origin "https://github.com/$(gh api user --jq .login)/$REPO_NAME.git" 2>/dev/null || true
    git push -u origin main 2>/dev/null || git push -u origin master
  }

echo ""
echo "✅ Código publicado no GitHub!"
echo "   https://github.com/$(gh api user --jq .login)/$REPO_NAME"
echo ""
echo "─────────────────────────────────────"
echo "📋 Próximo passo: deploy no VPS"
echo ""
echo "  ssh root@SEU_IP_VPS"
echo ""
echo "  # No VPS, cole e rode:"
echo "  curl -fsSL https://deb.nodesource.com/setup_22.x | bash - && apt-get install -y nodejs"
echo "  cd /var/www && git clone https://github.com/$(gh api user --jq .login)/$REPO_NAME.git && cd $REPO_NAME && npm install"
echo "  npm install -g pm2 && pm2 start \"node --experimental-sqlite server.js\" --name casa-jb && pm2 startup && pm2 save"
echo "─────────────────────────────────────"
echo ""

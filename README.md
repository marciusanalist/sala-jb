# Casa JB — Sistema de Agendamento de Salas

Aplicação web para agendamento de salas do Casa JB:

- **Sala de Reunião** — reservas por hora (08:00–20:00)
- **Salas de trabalho** — Postinho, Grumari, Meio da Barra, Ipanema, São Conrado, Leme (reserva dia inteiro)

---

## Pré-requisitos

- **Node.js v22.5+** (usa o SQLite embutido — sem dependências nativas)
- **Git**
- **PM2** para manter o servidor rodando (`npm install -g pm2`)

---

## Deploy no VPS Hostinger

### 1. Instalar Node.js 22 no VPS

```bash
# Conectar via SSH
ssh root@SEU_IP_VPS

# Instalar Node.js 22 via NodeSource
curl -fsSL https://deb.nodesource.com/setup_22.x | bash -
apt-get install -y nodejs

node --version  # deve mostrar v22.x.x
```

### 2. Clonar o repositório

```bash
cd /var/www
git clone https://github.com/SEU_USUARIO/casa-jb-agendamento.git
cd casa-jb-agendamento
npm install
```

### 3. Testar que funciona

```bash
node --experimental-sqlite server.js
# Deve mostrar: 🏛️  Casa JB Agendamento → http://localhost:3000
# Ctrl+C para sair
```

### 4. Rodar em produção com PM2

```bash
npm install -g pm2

# Iniciar a aplicação
pm2 start "node --experimental-sqlite server.js" --name casa-jb

# Garantir que reinicia no boot do servidor
pm2 startup
pm2 save
```

### 5. Configurar Nginx como proxy reverso

```bash
apt-get install -y nginx

# Criar configuração do site
nano /etc/nginx/sites-available/casa-jb
```

Cole o conteúdo abaixo (substituindo `SEU_DOMINIO.com` ou use o IP):

```nginx
server {
    listen 80;
    server_name SEU_DOMINIO.com;  # ou o IP do VPS

    location / {
        proxy_pass http://localhost:3000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

```bash
# Ativar o site
ln -s /etc/nginx/sites-available/casa-jb /etc/nginx/sites-enabled/
nginx -t
systemctl reload nginx
```

Agora acesse `http://SEU_DOMINIO_OU_IP` no navegador — o sistema estará online!

### 6. (Opcional) HTTPS com Let's Encrypt

```bash
apt-get install -y certbot python3-certbot-nginx
certbot --nginx -d SEU_DOMINIO.com
```

---

## Atualizar o sistema

Quando houver mudanças no código:

```bash
cd /var/www/casa-jb-agendamento
git pull
npm install
pm2 restart casa-jb
```

---

## Estrutura de arquivos

```
casa-jb-agendamento/
├── server.js          → API backend (Express + SQLite embutido)
├── package.json
├── .gitignore
├── data/              → Banco de dados SQLite (criado automaticamente, NÃO commitar)
│   └── bookings.db
└── public/
    └── index.html     → Frontend completo (HTML + CSS + JS)
```

---

## Comandos úteis

```bash
pm2 logs casa-jb        # Ver logs em tempo real
pm2 status              # Status da aplicação
pm2 restart casa-jb     # Reiniciar
pm2 stop casa-jb        # Parar

# Backup do banco de dados
cp /var/www/casa-jb-agendamento/data/bookings.db ~/backup_$(date +%Y%m%d).db
```

---

## API Endpoints

| Método | Rota | Descrição |
|--------|------|-----------|
| `GET` | `/api/rooms` | Lista todas as salas |
| `GET` | `/api/bookings?start=YYYY-MM-DD&end=YYYY-MM-DD` | Reservas no período |
| `POST` | `/api/bookings` | Criar reserva |
| `DELETE` | `/api/bookings/:id` | Cancelar reserva |

### POST /api/bookings — Sala de Reunião

```json
{
  "room_id": "reserva",
  "date": "2026-05-01",
  "start_time": "09:00",
  "end_time": "11:00",
  "person_name": "Maria Silva",
  "notes": "Sprint planning"
}
```

### POST /api/bookings — Salas de Trabalho

```json
{
  "room_id": "postinho",
  "date": "2026-05-01",
  "person_name": "João Pedro"
}
```

IDs das salas: `reserva`, `postinho`, `grumari`, `meio_da_barra`, `ipanema`, `sao_conrado`, `leme`

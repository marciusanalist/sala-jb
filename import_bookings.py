#!/usr/bin/env python3
"""
Casa JB — Importador de reservas
Fonte: planilha CASA_JB_Agendamento (Abril e Maio 2026)

Uso: python3 import_bookings.py
"""
import requests, time
from datetime import date, timedelta

BASE_URL = "https://sala-jb-production.up.railway.app"
DELAY    = 0.08  # segundos entre requests

# ─── Mapeamento de nomes ────────────────────────────────────
# Apelido/abreviação → nome completo cadastrado no sistema
NAME_MAP = {
    "Ariel":        "Ariel",
    "Daniel":       "Daniel",
    "Dudha":        "Dudha",
    "Erlanja":      "Erlanja",
    "Perez":        "João Perez",
    "João Perez":   "João Perez",
    "Jr":           "Juarez",
    "Junior":       "Juarez",
    "Matheus":      "Matheus Carvalho",
    "Ana":          "Ana Correia",
    "Mariana":      "Mariana Fernandes",
    "Bruna":        "Bruna Braga",
    "Nana":         "Anamaria",
    "André":        "André",
    "Priscila":     "Priscila",
    "Rodrigo":      "Rodrigo Moura",
    "Myllena":      "Myllena Vicente",
    "Felipe Peres": "Felipe Peres",
    "Julianna":     "Julianna Muniz",
    "Mari D.":      "Marianna Dias",
    "Marianna":     "Marianna Dias",
    "Mari":         "Marianna Dias",
    "Victor":       "Victor Chagas",
    "Giovana":      "Giovana Peralta",
    "Fernanda":     "Fernanda Manier",
    "Fernando":     "Fernando Fernandes",
    "Luiza":        "Luiza Miranda",
    "Carol":        "Caroline Dinucci",
    "Beatriz":      "Beatriz Mattos",
    "Rafa R.":      "Rafaela Riqueza",
    "Rafa":         "Rafaela Riqueza",
    "Tali":         "Talitha Caliman",
    "João":         "João Casotti",
    "Claudio":      "Claudio",
    "Rod":          "Rod",
    "Marcius":      "Marcius",
    "Bruno":        "Bruno Lins",
    "Liuzzi":       "Bruno Liuzzi",
    "Anamaria":     "Anamaria",
    "Anna":         "Anna Clara",
    "Edilson":      "Edilson",
    "Laura":        "Laura Muller",
    "Pat":          "Patricia Fanaia",
    "Ana Ju":       "Ana Julia Apostolides",
    "Anaju":        "Ana Julia Apostolides",
    "Ana Julia":    "Ana Julia Apostolides",
    "Mauro":        "Mauro",
    "Peu":          "Peu",
    # Nomes externos / clientes — mapeados como estão
    "EDGE ENGENHARIA": "EDGE ENGENHARIA",
}

SKIP = {None, "", "OBRA", "OBRAS", "Gestão Mamba", "Gestão SLB",
        "SAL + NATURA", "BIS", "reunião socios", "CSC", "Edição",
        "⚠️ A comprar", "Ilha de Edição"}

def R(n):
    if not n or n.strip() in SKIP: return None
    return NAME_MAP.get(n.strip(), n.strip())

# ─── Padrões semanais (0=Seg,1=Ter,2=Qua,3=Qui,4=Sex) ───────
# Baseado nos dados de Abril/Maio 2026 do PDF

WEEKLY = {
    # ── São Conrado ──────────────────────────────────────────
    "sao_conrado": {
        "p1": {0:"Marcius",  1:"Marcius",  2:"Marcius",  3:"Marcius",  4:"Marcius"},
        "p2": {0:"Bruno",    1:"Bruno",    2:"Bruno",    3:"Bruno",    4:"Bruno"},
        "p3": {0:"Claudio",              2:"Claudio",  3:"Claudio",  4:"Claudio"},
        "p4": {                                                       4:"Anna"},
    },
    # ── Leme (trabalha Seg–Qui, sem sexta) ───────────────────
    "leme": {
        "p1": {0:"Anna",    1:"Anna",    2:"André",  3:"Anna"},
        "p2": {0:"Tali",    1:"Tali",    2:"Tali",   3:"Tali"},
        "p3": {0:"João",    1:"Claudio", 2:"João",   3:"João"},
        "p4": {0:"Rod",     1:"Rod",     2:"Rod",    3:"Rod"},
    },
    # ── Ipanema ──────────────────────────────────────────────
    "ipanema": {
        "p01": {4:"Marianna", 0:"Rafa",    1:"Ana Ju",  2:"Carol",    3:"Julianna"},
        "p02": {4:"Giovana",  0:"Fernanda",1:"Luiza",   2:"Rafa",     3:"Luiza"},
        "p03": {4:"João",     0:"Carol",   1:"Anamaria",2:"Beatriz",  3:"Anamaria"},
        "p04": {0:"Victor",   1:"Victor",  2:"Victor",  3:"Beatriz",  4:"Victor"},
        "p05": {0:"Matheus",  1:"Pat",     2:"Matheus", 3:"Laura",    4:"Laura"},
        "p06": {0:"Fernando", 1:"Giovana", 2:"Fernanda",3:"Mari",     4:"Fernando"},
    },
    # ── Meio da Barra ─────────────────────────────────────────
    "meio_da_barra": {
        "p1": {4:"Matheus", 0:"Ana",     1:"Mariana", 2:"Bruna",   3:"Ana"},
        "p2": {4:"André",   0:"Jr",      1:"Bruna",   2:"Ana Ju",  3:"Jr"},
        "p3": {4:"Pat",     0:"Priscila",1:"Julianna",2:"Myllena", 3:"Priscila"},
        "p4": {             0:"Mariana", 1:"Rodrigo", 2:"Nana",    3:"Rodrigo"},
    },
    # ── Postinho ─────────────────────────────────────────────
    "postinho": {
        "p01": {0:"Erlanja", 1:"Daniel",   2:"Ariel",              4:"Ariel"},
        "p02": {0:"Erlanja", 1:"Daniel",                           4:"Daniel"},
        "p03": {             1:"Dudha",                3:"Erlanja"},
        "p04": {0:"Dudha"},
        "p05": {0:"Perez",   1:"Perez",    2:"Perez",  3:"Perez"},
    },
    # ── Grumari ──────────────────────────────────────────────
    "grumari": {
        "p1": {0:"EDGE ENGENHARIA",1:"EDGE ENGENHARIA",2:"EDGE ENGENHARIA",
               3:"EDGE ENGENHARIA",4:"EDGE ENGENHARIA"},
    },
}

# ─── Reunião: reservas pontuais extraídas do PDF (Abril 2026) ─
MEETING = [
    # (date, start, end, name)
    ("2026-04-01", "14:00", "16:00", "MAMBA"),
    ("2026-04-01", "16:00", "17:00", "SAL + NATURA"),
    ("2026-04-01", "17:00", "19:00", "reunião sócios"),
    ("2026-04-02", "14:00", "15:00", "STONE"),
    ("2026-04-02", "15:00", "17:00", "COMERCIAL"),
    ("2026-04-02", "17:00", "19:00", "reunião sócios"),
    ("2026-04-03", "10:00", "12:00", "SLB"),
    ("2026-04-03", "15:00", "16:00", "ENERGISA"),
    ("2026-04-03", "16:00", "17:00", "Comunicação"),
    ("2026-04-03", "17:00", "19:00", "reunião sócios"),
    ("2026-04-06", "14:00", "16:00", "MAMBA"),
    ("2026-04-06", "16:00", "17:00", "Branding"),
    ("2026-04-06", "17:00", "19:00", "reunião sócios"),
    ("2026-04-07", "10:00", "12:00", "SLB"),
    ("2026-04-07", "17:00", "18:00", "reunião sócios"),
    ("2026-04-08", "09:00", "13:00", "Reunião Conselho Business Exchange"),
    ("2026-04-20", "14:00", "16:00", "MAMBA"),
    ("2026-04-20", "17:00", "19:00", "reunião sócios"),
    ("2026-04-21", "17:00", "19:00", "reunião sócios"),
    ("2026-04-22", "17:00", "19:00", "reunião sócios"),
    ("2026-04-23", "16:00", "18:00", "BERSHKA"),
    ("2026-04-23", "17:00", "19:00", "Casa Carioca - Naming"),
    ("2026-04-24", "10:00", "12:00", "Reunião Edge Engenharia"),
    ("2026-04-24", "15:00", "16:00", "Entrevista Redatora"),
    ("2026-04-24", "16:00", "19:00", "Casa Carioca - Naming"),
    ("2026-04-27", "17:00", "19:00", "reunião sócios"),
    ("2026-04-28", "16:00", "18:00", "BERSHKA"),
    ("2026-04-28", "17:00", "19:00", "reunião sócios"),
    ("2026-04-29", "17:00", "19:00", "reunião sócios"),
    # Maio
    ("2026-05-07", "09:00", "13:00", "Reunião Conselho Business Exchange"),
    ("2026-05-15", "15:00", "17:00", "BIS Manual de Projetos"),
    ("2026-05-16", "15:00", "17:00", "BIS Manual de Projetos"),
]

# ─── Utilitários ─────────────────────────────────────────────
def weekdays_in(year, month):
    d, days = date(year, month, 1), []
    while d.month == month:
        if d.weekday() < 5:
            days.append(d)
        d += timedelta(1)
    return days

def post_booking(payload):
    r = requests.post(f"{BASE_URL}/api/bookings", json=payload, timeout=10)
    return r.status_code, r.text

# ─── Cadastrar novos nomes ────────────────────────────────────
NEW_NAMES = [
    "Dudha", "André", "Mauro", "Peu", "Felipe Peres",
    "Juarez", "Bruno Liuzzi", "EDGE ENGENHARIA",
    "reunião sócios", "STONE", "MAMBA", "ENERGISA",
    "Branding", "Comunicação", "SLB", "BERSHKA",
    "Casa Carioca - Naming", "Reunião Edge Engenharia",
    "Entrevista Redatora", "Reunião Conselho Business Exchange",
    "BIS Manual de Projetos",
]

print("=" * 55)
print("  Casa JB — Importador de Reservas")
print("=" * 55)
print()
print("📋 Registrando novos nomes...")
for n in NEW_NAMES:
    r = requests.post(f"{BASE_URL}/api/names", json={"name": n}, timeout=10)
    status = "✅" if r.status_code == 200 else "⚠️"
    print(f"  {status} {n}")
    time.sleep(0.05)

# ─── Importar mesas: Abril (já passado) + Maio ───────────────
print()
print("🪑 Importando reservas de mesas...")

ok = skip = err = 0

for year, month in [(2026, 4), (2026, 5)]:
    for d in weekdays_in(year, month):
        wd = d.weekday()
        ds = d.isoformat()
        for room_id, positions in WEEKLY.items():
            for pos_id, schedule in positions.items():
                raw = schedule.get(wd)
                name = R(raw)
                if not name:
                    continue
                payload = {
                    "room_id":     room_id,
                    "position_id": pos_id,
                    "date":        ds,
                    "person_name": name,
                }
                code, body = post_booking(payload)
                if code == 201:
                    ok += 1
                elif code == 409:
                    skip += 1   # já existe
                else:
                    err += 1
                    print(f"  ❌ {ds} {room_id}/{pos_id} [{name}]: {body[:80]}")
                time.sleep(DELAY)

print(f"  ✅ {ok} criadas  |  ⏭  {skip} já existiam  |  ❌ {err} erros")

# ─── Importar Sala de Reunião ─────────────────────────────────
print()
print("🤝 Importando reservas de reunião...")
ok2 = skip2 = err2 = 0

for (ds, st, en, person) in MEETING:
    payload = {
        "room_id":     "reserva",
        "date":        ds,
        "start_time":  st,
        "end_time":    en,
        "person_name": person,
    }
    code, body = post_booking(payload)
    if code == 201:
        ok2 += 1
    elif code == 409:
        skip2 += 1
    else:
        err2 += 1
        print(f"  ❌ {ds} {st}-{en} [{person}]: {body[:80]}")
    time.sleep(DELAY)

print(f"  ✅ {ok2} criadas  |  ⏭  {skip2} já existiam  |  ❌ {err2} erros")

# ─── Resumo ───────────────────────────────────────────────────
print()
print("=" * 55)
print(f"  TOTAL  →  {ok+ok2} reservas importadas com sucesso")
print("=" * 55)

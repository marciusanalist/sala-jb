// Requires Node.js >= 22.5 (node:sqlite built-in)
const { DatabaseSync } = require('node:sqlite');
const express = require('express');
const cors    = require('cors');
const path    = require('path');
const fs      = require('fs');

const app  = express();
const PORT = process.env.PORT || 3000;

// ─── Database ─────────────────────────────────────────────────────────────────
if (!fs.existsSync('./data')) fs.mkdirSync('./data');

const db = new DatabaseSync('./data/bookings.db');

db.exec(`
  CREATE TABLE IF NOT EXISTS bookings (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    room_id     TEXT NOT NULL,
    position_id TEXT,
    date        TEXT NOT NULL,
    start_time  TEXT,
    end_time    TEXT,
    person_name TEXT NOT NULL,
    notes       TEXT,
    created_at  TEXT DEFAULT (datetime('now', 'localtime'))
  );
  CREATE INDEX IF NOT EXISTS idx_date      ON bookings(date);
  CREATE INDEX IF NOT EXISTS idx_room_date ON bookings(room_id, date);
  CREATE INDEX IF NOT EXISTS idx_pos_date  ON bookings(room_id, position_id, date);
`);

// Migration: add position_id to existing databases
try { db.exec(`ALTER TABLE bookings ADD COLUMN position_id TEXT`); } catch(_) {}

// ─── Names ────────────────────────────────────────────────────────────────────
const DEFAULT_NAMES = [
  'Ana Correia', 'Ana Julia Apostolides', 'Anamaria', 'Anna Clara',
  'Ariel', 'Beatriz Mattos', 'Bruna Braga', 'Bruno Lins', 'Bruno Liuzzi',
  'Caroline Dinucci', 'Claudio', 'Daniel', 'Edilson', 'Erlanja',
  'Fernanda Manier', 'Fernando Fernandes', 'Giovana Peralta',
  'João Casotti', 'João Perez', 'Juarez', 'Julianna Muniz',
  'Koca', 'Laura Muller', 'Luiza Miranda', 'Marcelus', 'Marcius',
  'Maria Eduardha', 'Mariana Fernandes', 'Mariana Vasconcelos',
  'Marianna Dias', 'Matheus Carvalho', 'Myllena Vicente',
  'Patricia Fanaia', 'Priscila', 'Rafaela Riqueza', 'Rod',
  'Rodrigo Moura', 'Talitha Caliman', 'Victor Chagas',
];

const NAMES_FILE = './data/names.json';

function loadNames() {
  try {
    if (fs.existsSync(NAMES_FILE))
      return JSON.parse(fs.readFileSync(NAMES_FILE, 'utf8'));
  } catch(_) {}
  return [...DEFAULT_NAMES];
}

function saveNames(names) {
  fs.writeFileSync(NAMES_FILE, JSON.stringify(names, null, 2));
}

if (!fs.existsSync(NAMES_FILE)) saveNames(DEFAULT_NAMES);

// ─── Rooms & Positions ────────────────────────────────────────────────────────
const ROOMS = [
  {
    id: 'reserva', name: 'Sala de Reunião', floor: null, type: 'meeting',
    positions: []
  },
  {
    id: 'postinho', name: 'Postinho', floor: 1, type: 'desk',
    positions: [
      { id: 'p01', label: 'Posição 01' },
      { id: 'p02', label: 'Posição 02' },
      { id: 'p03', label: 'Posição 03' },
      { id: 'p04', label: 'Posição 04' },
      { id: 'p05', label: 'Posição 05' },
      { id: 'p06', label: 'Posição 06' },
    ]
  },
  {
    id: 'grumari', name: 'Grumari', floor: 1, type: 'desk',
    positions: [
      { id: 'p1', label: 'Posição 1' },
      { id: 'p2', label: 'Posição 2' },
      { id: 'p3', label: 'Posição 3' },
      { id: 'p4', label: 'Posição 4' },
    ]
  },
  {
    id: 'meio_da_barra', name: 'Meio da Barra', floor: 1, type: 'desk',
    positions: [
      { id: 'p1', label: 'Posição 1' },
      { id: 'p2', label: 'Posição 2' },
      { id: 'p3', label: 'Posição 3' },
      { id: 'p4', label: 'Posição 4' },
    ]
  },
  {
    id: 'ipanema', name: 'Ipanema', floor: 2, type: 'desk',
    positions: [
      { id: 'p01', label: 'Posição 01' },
      { id: 'p02', label: 'Posição 02' },
      { id: 'p03', label: 'Posição 03', equipment: 'iMac 030' },
      { id: 'p04', label: 'Posição 04', equipment: 'Mac Mini 086' },
      { id: 'p05', label: 'Posição 05', equipment: 'Mac Mini 085' },
      { id: 'p06', label: 'Posição 06', equipment: 'PC 072' },
    ]
  },
  {
    id: 'sao_conrado', name: 'São Conrado', floor: 2, type: 'desk',
    positions: [
      { id: 'p1', label: 'Posição 1' },
      { id: 'p2', label: 'Posição 2' },
      { id: 'p3', label: 'Posição 3' },
      { id: 'p4', label: 'Posição 4' },
    ]
  },
  {
    id: 'leme', name: 'Leme', floor: 2, type: 'desk',
    positions: [
      { id: 'p1', label: 'Posição 1' },
      { id: 'p2', label: 'Posição 2' },
      { id: 'p3', label: 'Posição 3' },
      { id: 'p4', label: 'Posição 4' },
    ]
  },
];

const ROOM_MAP = Object.fromEntries(ROOMS.map(r => [r.id, r]));

// ─── Middleware ────────────────────────────────────────────────────────────────
app.use(cors());
app.use(express.json());
app.use(express.static(path.join(__dirname, 'public')));

// ─── Prepared statements ──────────────────────────────────────────────────────
const stmts = {
  listRange: db.prepare(`
    SELECT id, room_id, position_id, date, start_time, end_time, person_name, notes, created_at
    FROM bookings WHERE date >= ? AND date <= ?
    ORDER BY date, room_id, position_id, start_time
  `),
  conflictMeeting: db.prepare(`
    SELECT id, person_name, start_time, end_time FROM bookings
    WHERE room_id = ? AND date = ? AND start_time < ? AND end_time > ?
  `),
  conflictDesk: db.prepare(`
    SELECT id, person_name FROM bookings
    WHERE room_id = ? AND position_id = ? AND date = ?
  `),
  insert: db.prepare(`
    INSERT INTO bookings (room_id, position_id, date, start_time, end_time, person_name, notes)
    VALUES (?, ?, ?, ?, ?, ?, ?)
  `),
  getOne: db.prepare('SELECT * FROM bookings WHERE id = ?'),
  delete:  db.prepare('DELETE FROM bookings WHERE id = ?'),
};

// ─── Routes ───────────────────────────────────────────────────────────────────

app.get('/api/rooms', (_req, res) => res.json(ROOMS));

// Names
app.get('/api/names', (_req, res) => res.json(loadNames()));

app.post('/api/names', (req, res) => {
  const { name } = req.body ?? {};
  if (!name?.trim()) return res.status(400).json({ error: 'Nome inválido' });
  const names = loadNames();
  const clean = name.trim();
  if (!names.includes(clean)) { names.push(clean); names.sort(); saveNames(names); }
  res.json(loadNames());
});

app.delete('/api/names/:name', (req, res) => {
  const target = decodeURIComponent(req.params.name);
  const names = loadNames().filter(n => n !== target);
  saveNames(names);
  res.json(loadNames());
});

// Bookings
app.get('/api/bookings', (req, res) => {
  const { start, end } = req.query;
  if (!start || !end) return res.status(400).json({ error: 'start e end são obrigatórios' });
  res.json(stmts.listRange.all(start, end));
});

app.post('/api/bookings', (req, res) => {
  const { room_id, position_id, date, start_time, end_time, person_name, notes } = req.body ?? {};

  if (!room_id || !date || !person_name?.trim())
    return res.status(400).json({ error: 'room_id, date e person_name são obrigatórios' });

  const room = ROOM_MAP[room_id];
  if (!room) return res.status(400).json({ error: 'Sala inválida' });

  if (!/^\d{4}-\d{2}-\d{2}$/.test(date))
    return res.status(400).json({ error: 'Formato de data inválido' });

  if (room.type === 'meeting') {
    if (!start_time || !end_time)
      return res.status(400).json({ error: 'Horários obrigatórios para a Sala de Reunião' });
    if (start_time >= end_time)
      return res.status(400).json({ error: 'Horário de fim deve ser após o início' });

    const c = stmts.conflictMeeting.get(room_id, date, end_time, start_time);
    if (c) return res.status(409).json({
      error: `Horário já reservado por ${c.person_name} (${c.start_time}–${c.end_time})`
    });
  } else {
    if (!position_id)
      return res.status(400).json({ error: 'position_id é obrigatório para salas de trabalho' });

    const pos = room.positions.find(p => p.id === position_id);
    if (!pos) return res.status(400).json({ error: 'Posição inválida' });

    const c = stmts.conflictDesk.get(room_id, position_id, date);
    if (c) return res.status(409).json({
      error: `Posição já reservada por ${c.person_name} neste dia`
    });
  }

  const result = stmts.insert.run(
    room_id,
    room.type === 'meeting' ? null : position_id,
    date,
    room.type === 'meeting' ? start_time : null,
    room.type === 'meeting' ? end_time   : null,
    person_name.trim(),
    notes?.trim() || null
  );

  // Auto-save new names
  const names = loadNames();
  const clean = person_name.trim();
  if (!names.includes(clean)) { names.push(clean); names.sort(); saveNames(names); }

  res.status(201).json(stmts.getOne.get(result.lastInsertRowid));
});

app.delete('/api/bookings/:id', (req, res) => {
  const id = Number(req.params.id);
  if (!stmts.getOne.get(id)) return res.status(404).json({ error: 'Reserva não encontrada' });
  stmts.delete.run(id);
  res.json({ success: true });
});

// ─── Frequency / Attendance ───────────────────────────────────────────────────
app.get('/api/frequency', (req, res) => {
  const { year, month } = req.query;
  if (!year || !month) return res.status(400).json({ error: 'year e month obrigatórios' });

  const y = parseInt(year), m = parseInt(month);
  if (isNaN(y) || isNaN(m) || m < 1 || m > 12)
    return res.status(400).json({ error: 'Parâmetros inválidos' });

  const pad = n => String(n).padStart(2, '0');
  const start = `${y}-${pad(m)}-01`;
  const lastDay = new Date(y, m, 0).getDate();
  const end = `${y}-${pad(m)}-${pad(lastDay)}`;

  // DISTINCT person+date: deduplicates multiple bookings on same day
  const rows = db.prepare(`
    SELECT DISTINCT person_name, date
    FROM bookings
    WHERE date >= ? AND date <= ?
      AND room_id != 'reserva'
    ORDER BY person_name, date
  `).all(start, end);

  // Group by person
  const personMap = {};
  rows.forEach(({ person_name, date }) => {
    if (!personMap[person_name]) personMap[person_name] = [];
    personMap[person_name].push(date);
  });

  const people = Object.entries(personMap)
    .map(([name, dates]) => ({ name, days: dates.length, dates }))
    .sort((a, b) => b.days - a.days);

  // Daily count of unique people (for heatmap)
  const daily = {};
  rows.forEach(({ date }) => { daily[date] = (daily[date] || 0) + 1; });

  res.json({ year: y, month: m, people, daily });
});

// Fallback → SPA
app.get('*', (_req, res) => {
  res.sendFile(path.join(__dirname, 'public', 'index.html'));
});

app.listen(PORT, () => {
  console.log(`🏛️  Casa JB Agendamento → http://localhost:${PORT}`);
});

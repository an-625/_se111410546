const express = require('express');
const cors = require('cors');
const { Pool } = require('pg');
const os = require('os');

const app = express();
app.use(cors());
app.use(express.json());

const PORT = process.env.PORT || 3000;
const pool = new Pool({ connectionString: process.env.DATABASE_URL || 'postgres://micro:micro123@postgres:5432/microdb' });

async function dbInfo() {
  try {
    const v = await pool.query('SELECT version() AS ver');
    const c = await pool.query('SELECT COUNT(*)::int AS count FROM visits');
    return { connected: true, postgres_version: v.rows[0].ver, visits_count: c.rows[0].count };
  } catch (e) {
    return { connected: false, error: e.message };
  }
}

app.get('/health', (req, res) => {
  res.json({ status: 'ok', service: 'api-node', language: 'Node.js 20 + Express', timestamp: new Date().toISOString() });
});

app.get('/info', async (req, res) => {
  res.json({
    service: 'api-node', language: 'Node.js', framework: 'Express',
    hostname: os.hostname(), node_version: process.version,
    db: await dbInfo(), timestamp: new Date().toISOString()
  });
});

app.get('/visits', async (req, res) => {
  try {
    const r = await pool.query('SELECT id, service, created_at FROM visits ORDER BY id DESC LIMIT 10');
    res.json({ service: 'api-node', rows: r.rows });
  } catch (e) { res.status(500).json({ error: e.message }); }
});

app.post('/visits', async (req, res) => {
  try {
    const r = await pool.query("INSERT INTO visits(service) VALUES('node') RETURNING *");
    res.json({ inserted: r.rows[0] });
  } catch (e) { res.status(500).json({ error: e.message }); }
});

app.get('/', (req, res) => res.redirect('/health'));

app.listen(PORT, '0.0.0.0', () => console.log(`node listening on ${PORT}`));

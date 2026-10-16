import os, socket, datetime
import psycopg2
from flask import Flask, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

DB_URL = os.environ.get("DATABASE_URL", "postgres://micro:micro123@postgres:5432/microdb")
PORT = int(os.environ.get("PORT", "5000"))

def db_info():
    try:
        conn = psycopg2.connect(DB_URL)
        cur = conn.cursor()
        cur.execute("SELECT version();")
        ver = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM visits;")
        count = cur.fetchone()[0]
        cur.close(); conn.close()
        return {"connected": True, "postgres_version": ver, "visits_count": count}
    except Exception as e:
        return {"connected": False, "error": str(e)}

@app.get("/health")
def health():
    return jsonify(status="ok", service="api-python", language="Python 3.12 + Flask",
                   timestamp=datetime.datetime.utcnow().isoformat() + "Z")

@app.get("/info")
def info():
    import sys
    return jsonify(service="api-python", language="Python", framework="Flask",
                   python_version=sys.version.split()[0],
                   hostname=socket.gethostname(), db=db_info(),
                   timestamp=datetime.datetime.utcnow().isoformat() + "Z")

@app.get("/visits")
def visits():
    try:
        conn = psycopg2.connect(DB_URL); cur = conn.cursor()
        cur.execute("SELECT id, service, created_at FROM visits ORDER BY id DESC LIMIT 10;")
        rows = [{"id": r[0], "service": r[1], "created_at": str(r[2])} for r in cur.fetchall()]
        cur.close(); conn.close()
        return jsonify(service="api-python", rows=rows)
    except Exception as e:
        return jsonify(error=str(e)), 500

@app.post("/visits")
def add_visit():
    try:
        conn = psycopg2.connect(DB_URL); cur = conn.cursor()
        cur.execute("INSERT INTO visits(service) VALUES('python') RETURNING id, service, created_at;")
        r = cur.fetchone(); conn.commit()
        cur.close(); conn.close()
        return jsonify(inserted={"id": r[0], "service": r[1], "created_at": str(r[2])})
    except Exception as e:
        return jsonify(error=str(e)), 500

@app.get("/")
def root():
    return jsonify(status="ok", service="api-python")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=PORT)

import sqlite3, time, os
from config import DB_PATH

def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

def init_db():
    conn = get_conn(); c = conn.cursor()
    c.execute("""CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT NOT NULL UNIQUE,
        email TEXT NOT NULL UNIQUE,
        password_hash TEXT NOT NULL,
        created_at REAL NOT NULL)""")
    c.execute("""CREATE TABLE IF NOT EXISTS projects (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        owner_id INTEGER NOT NULL,
        name TEXT NOT NULL UNIQUE,
        description TEXT DEFAULT '',
        dataset_path TEXT NOT NULL,
        dataset_name TEXT NOT NULL,
        created_at REAL NOT NULL,
        FOREIGN KEY(owner_id) REFERENCES users(id))""")
    c.execute("""CREATE TABLE IF NOT EXISTS submissions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        project_id INTEGER NOT NULL,
        user_id INTEGER NOT NULL,
        model_filename TEXT NOT NULL,
        model_path TEXT NOT NULL,
        model_hash TEXT NOT NULL,
        verified_accuracy REAL NOT NULL,
        combined_hash TEXT NOT NULL,
        eth_tx_hash TEXT NOT NULL,
        eth_tx_url TEXT NOT NULL,
        eth_mode TEXT NOT NULL DEFAULT 'mock',
        block_index INTEGER NOT NULL,
        previous_hash TEXT NOT NULL,
        submitted_at REAL NOT NULL,
        FOREIGN KEY(project_id) REFERENCES projects(id),
        FOREIGN KEY(user_id) REFERENCES users(id))""")
    conn.commit(); conn.close()

def create_user(username, email, pw_hash):
    conn = get_conn()
    try:
        conn.execute("INSERT INTO users (username,email,password_hash,created_at) VALUES (?,?,?,?)",
                     (username.strip(), email.strip().lower(), pw_hash, time.time()))
        conn.commit(); return True, None
    except sqlite3.IntegrityError as e:
        return False, ("Username already taken." if "username" in str(e) else "Email already registered.")
    finally:
        conn.close()

def get_user_by_id(uid):
    conn = get_conn()
    row = conn.execute("SELECT * FROM users WHERE id=?", (uid,)).fetchone()
    conn.close(); return dict(row) if row else None

def get_user_by_username(u):
    conn = get_conn()
    row = conn.execute("SELECT * FROM users WHERE username=?", (u.strip(),)).fetchone()
    conn.close(); return dict(row) if row else None

def get_user_by_email(e):
    conn = get_conn()
    row = conn.execute("SELECT * FROM users WHERE email=?", (e.strip().lower(),)).fetchone()
    conn.close(); return dict(row) if row else None

def create_project(owner_id, name, description, dataset_path, dataset_name):
    conn = get_conn()
    try:
        conn.execute("INSERT INTO projects (owner_id,name,description,dataset_path,dataset_name,created_at) VALUES (?,?,?,?,?,?)",
                     (owner_id, name.strip(), description.strip(), dataset_path, dataset_name, time.time()))
        conn.commit(); return True, None
    except sqlite3.IntegrityError:
        return False, "A project with that name already exists."
    finally:
        conn.close()

def get_all_projects():
    conn = get_conn()
    rows = conn.execute("""SELECT p.*, u.username AS owner_name, COUNT(s.id) AS submission_count
        FROM projects p JOIN users u ON p.owner_id=u.id
        LEFT JOIN submissions s ON s.project_id=p.id
        GROUP BY p.id ORDER BY p.created_at DESC""").fetchall()
    conn.close(); return [dict(r) for r in rows]

def get_project(pid):
    conn = get_conn()
    row = conn.execute("""SELECT p.*, u.username AS owner_name
        FROM projects p JOIN users u ON p.owner_id=u.id WHERE p.id=?""", (pid,)).fetchone()
    conn.close(); return dict(row) if row else None

def delete_project(pid):
    conn = get_conn()
    for r in conn.execute("SELECT model_path FROM submissions WHERE project_id=?", (pid,)).fetchall():
        try:
            if os.path.exists(r["model_path"]): os.remove(r["model_path"])
        except: pass
    proj = conn.execute("SELECT dataset_path FROM projects WHERE id=?", (pid,)).fetchone()
    if proj and os.path.exists(proj["dataset_path"]):
        try: os.remove(proj["dataset_path"])
        except: pass
    conn.execute("DELETE FROM submissions WHERE project_id=?", (pid,))
    conn.execute("DELETE FROM projects WHERE id=?", (pid,))
    conn.commit(); conn.close()

def count_outside_submissions(pid, owner_id):
    conn = get_conn()
    row = conn.execute("SELECT COUNT(*) AS cnt FROM submissions WHERE project_id=? AND user_id!=?", (pid, owner_id)).fetchone()
    conn.close(); return row["cnt"] if row else 0

def get_project_submissions(pid):
    conn = get_conn()
    rows = conn.execute("""SELECT s.*, u.username FROM submissions s
        JOIN users u ON s.user_id=u.id WHERE s.project_id=?
        ORDER BY s.verified_accuracy DESC, s.submitted_at ASC""", (pid,)).fetchall()
    conn.close(); return [dict(r) for r in rows]

def get_latest_submission_hash(pid):
    conn = get_conn()
    row = conn.execute("SELECT combined_hash FROM submissions WHERE project_id=? ORDER BY block_index DESC LIMIT 1", (pid,)).fetchone()
    conn.close()
    if row: return row["combined_hash"]
    import hashlib, json
    return hashlib.sha256(json.dumps({"genesis": True, "project_id": pid}, sort_keys=True).encode()).hexdigest()

def get_next_block_index(pid):
    conn = get_conn()
    row = conn.execute("SELECT COUNT(*) AS cnt FROM submissions WHERE project_id=?", (pid,)).fetchone()
    conn.close(); return (row["cnt"] if row else 0) + 1

def save_submission(project_id, user_id, model_filename, model_path, model_hash,
                    verified_accuracy, combined_hash, eth_tx_hash, eth_tx_url,
                    eth_mode, block_index, previous_hash, submitted_at):  # ← add submitted_at
    conn = get_conn()
    conn.execute("""INSERT INTO submissions
        (project_id,user_id,model_filename,model_path,model_hash,verified_accuracy,
         combined_hash,eth_tx_hash,eth_tx_url,eth_mode,block_index,previous_hash,submitted_at)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)""",
        (project_id, user_id, model_filename, model_path, model_hash, verified_accuracy,
         combined_hash, eth_tx_hash, eth_tx_url, eth_mode, block_index, previous_hash,
         submitted_at))  # ← use passed value, not time.time()
    conn.commit(); conn.close()

def get_submission(sid):
    conn = get_conn()
    row = conn.execute("""SELECT s.*, u.username, p.name AS project_name, p.id AS project_id
        FROM submissions s JOIN users u ON s.user_id=u.id JOIN projects p ON s.project_id=p.id
        WHERE s.id=?""", (sid,)).fetchone()
    conn.close(); return dict(row) if row else None

def get_user_submissions(uid):
    conn = get_conn()
    rows = conn.execute("""SELECT s.*, p.name AS project_name FROM submissions s
        JOIN projects p ON s.project_id=p.id WHERE s.user_id=?
        ORDER BY s.submitted_at DESC""", (uid,)).fetchall()
    conn.close(); return [dict(r) for r in rows]

def get_user_projects(uid):
    conn = get_conn()
    rows = conn.execute("""SELECT p.*, COUNT(s.id) AS submission_count FROM projects p
        LEFT JOIN submissions s ON s.project_id=p.id WHERE p.owner_id=?
        GROUP BY p.id ORDER BY p.created_at DESC""", (uid,)).fetchall()
    conn.close(); return [dict(r) for r in rows]

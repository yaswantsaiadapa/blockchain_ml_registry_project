import sqlite3
import json
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "chainml.db")


def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_conn()
    c = conn.cursor()

    # Projects table
    c.execute("""
        CREATE TABLE IF NOT EXISTS projects (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            description TEXT DEFAULT '',
            created_at REAL NOT NULL
        )
    """)

    # Blocks table — one row per block (including genesis)
    c.execute("""
        CREATE TABLE IF NOT EXISTS blocks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            project_id INTEGER NOT NULL,
            block_index INTEGER NOT NULL,
            timestamp REAL NOT NULL,
            previous_hash TEXT NOT NULL,
            block_hash TEXT NOT NULL,
            data TEXT NOT NULL,
            FOREIGN KEY(project_id) REFERENCES projects(id)
        )
    """)

    conn.commit()
    conn.close()


# ---------- PROJECT CRUD ----------

def create_project(name: str, description: str = "") -> int:
    import time
    conn = get_conn()
    c = conn.cursor()
    c.execute(
        "INSERT INTO projects (name, description, created_at) VALUES (?, ?, ?)",
        (name.strip(), description.strip(), time.time())
    )
    project_id = c.lastrowid

    # Create genesis block for this project
    from blockchain import Block
    genesis = Block(0, {"info": "Genesis Block"}, "0")
    c.execute("""
        INSERT INTO blocks (project_id, block_index, timestamp, previous_hash, block_hash, data)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (project_id, genesis.index, genesis.timestamp,
          genesis.previous_hash, genesis.hash,
          json.dumps(genesis.data)))

    conn.commit()
    conn.close()
    return project_id


def get_all_projects():
    conn = get_conn()
    rows = conn.execute(
        "SELECT * FROM projects ORDER BY created_at DESC"
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_project(project_id: int):
    conn = get_conn()
    row = conn.execute(
        "SELECT * FROM projects WHERE id = ?", (project_id,)
    ).fetchone()
    conn.close()
    return dict(row) if row else None


def project_exists(name: str) -> bool:
    conn = get_conn()
    row = conn.execute(
        "SELECT id FROM projects WHERE name = ?", (name.strip(),)
    ).fetchone()
    conn.close()
    return row is not None


# ---------- BLOCK CRUD ----------

def save_block(project_id: int, block) -> None:
    conn = get_conn()
    conn.execute("""
        INSERT INTO blocks (project_id, block_index, timestamp, previous_hash, block_hash, data)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (project_id, block.index, block.timestamp,
          block.previous_hash, block.hash,
          json.dumps(block.data)))
    conn.commit()
    conn.close()


def load_blocks(project_id: int) -> list:
    """Return list of block dicts ordered by block_index."""
    conn = get_conn()
    rows = conn.execute(
        "SELECT * FROM blocks WHERE project_id = ? ORDER BY block_index ASC",
        (project_id,)
    ).fetchall()
    conn.close()
    result = []
    for r in rows:
        d = dict(r)
        d["data"] = json.loads(d["data"])
        result.append(d)
    return result


def get_project_model_count(project_id: int) -> int:
    conn = get_conn()
    row = conn.execute(
        "SELECT COUNT(*) as cnt FROM blocks WHERE project_id = ? AND block_index > 0",
        (project_id,)
    ).fetchone()
    conn.close()
    return row["cnt"] if row else 0

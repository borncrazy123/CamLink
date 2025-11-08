import sqlite3
from typing import Optional, List, Dict, Any
from pathlib import Path


DB_PATH = Path(__file__).resolve().parents[2] / 'camlink.db'


def get_connection(db_path: Path = DB_PATH) -> sqlite3.Connection:
	"""Return a sqlite3 connection with sensible defaults."""
	conn = sqlite3.connect(str(db_path), timeout=30)
	conn.row_factory = sqlite3.Row
	return conn


def init_task_table(db_path: Path = DB_PATH) -> None:
	"""Create tasks table if it does not exist."""
	schema = """
	CREATE TABLE IF NOT EXISTS tasks (
		id INTEGER PRIMARY KEY AUTOINCREMENT,
		clientid TEXT NOT NULL,
		requestid TEXT UNIQUE NOT NULL,
		requesttype TEXT,
		state TEXT,
		description TEXT,
		created_at TEXT DEFAULT (datetime('now')),
		updated_at TEXT
	);
	"""
	db_path.parent.mkdir(parents=True, exist_ok=True)
	with get_connection(db_path) as conn:
		conn.executescript(schema)


def drop_task_table(db_path: Path = DB_PATH) -> None:
	"""Drop the `tasks` table if it exists. Use with caution (data loss)."""
	with get_connection(db_path) as conn:
		conn.execute("DROP TABLE IF EXISTS tasks")

def create_task(data: Dict[str, Any], db_path: Path = DB_PATH) -> int:
	"""Insert a task row. Returns inserted row id.

	Required keys: clientid, requestid
	Optional: requesttype, state, description
	"""
	sql = """
	INSERT INTO tasks (clientid, requestid, requesttype, state, description, updated_at)
	VALUES (:clientid, :requestid, :requesttype, :state, :description, :updated_at)
	"""
	with get_connection(db_path) as conn:
		cur = conn.execute(sql, {
			'clientid': data['clientid'],
			'requestid': data['requestid'],
			'requesttype': data.get('requesttype'),
			'state': data.get('state'),
			'description': data.get('description'),
			'updated_at': data.get('updated_at')
		})
		return cur.lastrowid


def get_task_by_requestid(requestid: str, db_path: Path = DB_PATH) -> Optional[Dict[str, Any]]:
	sql = "SELECT * FROM tasks WHERE requestid = ?"
	with get_connection(db_path) as conn:
		cur = conn.execute(sql, (requestid,))
		row = cur.fetchone()
		return dict(row) if row else None


def list_tasks(clientid: Optional[str] = None, limit: int = 200, db_path: Path = DB_PATH) -> List[Dict[str, Any]]:
	if clientid:
		sql = "SELECT * FROM tasks WHERE clientid = ? ORDER BY id DESC LIMIT ?"
		params = (clientid, limit)
	else:
		sql = "SELECT * FROM tasks ORDER BY id DESC LIMIT ?"
		params = (limit,)
	with get_connection(db_path) as conn:
		cur = conn.execute(sql, params)
		return [dict(r) for r in cur.fetchall()]


def update_task(requestid: str, patch: Dict[str, Any], db_path: Path = DB_PATH) -> int:
	"""Update task fields by requestid. Returns number of rows updated."""
	allowed = ['clientid', 'requesttype', 'state', 'description', 'updated_at']
	sets = []
	params = {}
	for k, v in patch.items():
		if k in allowed:
			sets.append(f"{k} = :{k}")
			params[k] = v
	if not sets:
		return 0
	params['requestid'] = requestid
	sql = f"UPDATE tasks SET {', '.join(sets)} WHERE requestid = :requestid"
	with get_connection(db_path) as conn:
		cur = conn.execute(sql, params)
		return cur.rowcount


def delete_task(requestid: str, db_path: Path = DB_PATH) -> int:
	sql = "DELETE FROM tasks WHERE requestid = ?"
	with get_connection(db_path) as conn:
		cur = conn.execute(sql, (requestid,))
		return cur.rowcount


if __name__ == '__main__':
	print('Initializing task table at', DB_PATH)
	init_task_table()
	print('Inserting sample task...')
	tid = create_task({
		'clientid': 'CAM-1730985600000-ABC123',
		'requestid': 'REQ-0001',
		'requesttype': 'start_record',
		'state': 'calling',
		'description': '启动录制命令已下发',
		'updated_at': '2025-11-08 10:00:00'
	})
	print('Inserted task id:', tid)
	print('Listing tasks:')
	for t in list_tasks():
		print(t['requestid'], t['clientid'], t['state'])

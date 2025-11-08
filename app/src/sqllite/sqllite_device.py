import sqlite3
from typing import Optional, List, Dict, Any
from pathlib import Path


DB_PATH = Path(__file__).resolve().parents[2] / 'camlink.db'


def get_connection(db_path: Path = DB_PATH) -> sqlite3.Connection:
	"""Return a sqlite3 connection with sensible defaults."""
	conn = sqlite3.connect(str(db_path), timeout=30)
	conn.row_factory = sqlite3.Row
	return conn


def init_db(db_path: Path = DB_PATH) -> None:
	"""Create tables if they do not exist.

	Creates a `devices` table suitable for storing basic device info used
	by the demo pages.
	"""
	schema = """
	CREATE TABLE IF NOT EXISTS devices (
		id INTEGER PRIMARY KEY AUTOINCREMENT,
		hardware_id TEXT UNIQUE NOT NULL,
		client_id TEXT,
		hotel TEXT,
		location TEXT,
		wifi TEXT,
		runtime TEXT,
		fw TEXT,
		last_online TEXT,
		status TEXT,
		left_storage INTEGER,
		electric_percent INTEGER,
		network_signal_strength INTEGER
	);
	"""
	db_path.parent.mkdir(parents=True, exist_ok=True)
	with get_connection(db_path) as conn:
		conn.executescript(schema)

		# Ensure newer columns exist (safe to run multiple times)
		cur = conn.execute("PRAGMA table_info(devices)")
		cols = {r['name'] for r in cur.fetchall()}
		extras = {
			'status': 'TEXT',
			'run_state': 'TEXT',
			'left_storage': 'INTEGER',
			'electric_percent': 'INTEGER',
			'network_signal_strength': 'INTEGER'
		}
		for name, typ in extras.items():
			if name not in cols:
				conn.execute(f"ALTER TABLE devices ADD COLUMN {name} {typ}")


def insert_device(data: Dict[str, Any], db_path: Path = DB_PATH) -> int:
	"""Insert a device row. Returns the inserted row id.

	data keys: hardware_id (required), client_id, hotel, location, wifi, runtime, fw, last_online
	"""
	sql = """
	INSERT INTO devices (hardware_id, client_id, hotel, location, wifi, runtime, fw, last_online)
	VALUES (:hardware_id, :client_id, :hotel, :location, :wifi, :runtime, :fw, :last_online)
	"""
	with get_connection(db_path) as conn:
		cur = conn.execute(sql, {
			'hardware_id': data['hardware_id'],
			'client_id': data.get('client_id'),
			'hotel': data.get('hotel'),
			'location': data.get('location'),
			'wifi': data.get('wifi'),
			'runtime': data.get('runtime'),
			'fw': data.get('fw'),
			'last_online': data.get('last_online')
		})
		rowid = cur.lastrowid

		# If optional new fields provided, update them (INSERT with missing columns for compatibility)
		patch = {}
		if 'status' in data:
			patch['status'] = data['status']
		if 'run_state' in data:
			patch['run_state'] = data['run_state']
		if 'left_storage' in data:
			patch['left_storage'] = data['left_storage']
		if 'electric_percent' in data:
			patch['electric_percent'] = data['electric_percent']
		if 'network_signal_strength' in data:
			patch['network_signal_strength'] = data['network_signal_strength']
		if patch:
			# update the newly inserted row
			conn.execute(
				f"UPDATE devices SET " + ", ".join([f"{k} = :{k}" for k in patch.keys()]) + " WHERE id = :id",
				{**patch, 'id': rowid}
			)
		return rowid


def get_device(hardware_id: str, db_path: Path = DB_PATH) -> Optional[Dict[str, Any]]:
	sql = "SELECT * FROM devices WHERE hardware_id = ?"
	with get_connection(db_path) as conn:
		cur = conn.execute(sql, (hardware_id,))
		row = cur.fetchone()
		return dict(row) if row else None


def get_device_by_client_id(client_id: str, db_path: Path = DB_PATH) -> Optional[Dict[str, Any]]:
	"""通过client_id查询设备"""
	sql = "SELECT * FROM devices WHERE client_id = ?"
	with get_connection(db_path) as conn:
		cur = conn.execute(sql, (client_id,))
		row = cur.fetchone()
		return dict(row) if row else None


def get_client_id_by_hardware_id(hardware_id: str, db_path: Path = DB_PATH) -> Optional[str]:
	"""通过hardware_id获取client_id"""
	sql = "SELECT client_id FROM devices WHERE hardware_id = ?"
	with get_connection(db_path) as conn:
		cur = conn.execute(sql, (hardware_id,))
		row = cur.fetchone()
		return row['client_id'] if row else None


def list_devices(limit: int = 100, db_path: Path = DB_PATH) -> List[Dict[str, Any]]:
	sql = "SELECT * FROM devices ORDER BY id DESC LIMIT ?"
	with get_connection(db_path) as conn:
		cur = conn.execute(sql, (limit,))
		return [dict(r) for r in cur.fetchall()]


def update_device(hardware_id: str, patch: Dict[str, Any], db_path: Path = DB_PATH) -> int:
	"""Update device fields. Returns number of rows updated."""
	allowed = ['client_id', 'hotel', 'location', 'wifi', 'runtime', 'fw', 'last_online', 'status', 'run_state', 'left_storage', 'electric_percent', 'network_signal_strength']
	sets = []
	params = {}
	for k, v in patch.items():
		if k in allowed:
			sets.append(f"{k} = :{k}")
			params[k] = v
	if not sets:
		return 0
	params['hardware_id'] = hardware_id
	sql = f"UPDATE devices SET {', '.join(sets)} WHERE hardware_id = :hardware_id"
	with get_connection(db_path) as conn:
		cur = conn.execute(sql, params)
		return cur.rowcount

def delete_device(hardware_id: str, db_path: Path = DB_PATH) -> int:
	sql = "DELETE FROM devices WHERE hardware_id = ?"
	with get_connection(db_path) as conn:
		cur = conn.execute(sql, (hardware_id,))
		return cur.rowcount
	
if __name__ == '__main__':
	# small demo when run as script
	print('Initializing DB at', DB_PATH)
	init_db()
	print('Inserting sample device...')
	sid = insert_device({
		'hardware_id': 'HW-2024-001',
		'client_id': 'CAM-1730985600000-ABC123',
		'hotel': '北京希尔顿酒店',
		'location': '大堂入口',
		'wifi': 'Hotel-IoT-Network',
		'runtime': '15天 8小时',
		'fw': 'v2.1.3',
		'last_online': '2025-11-08 08:46:00',
		'status': '在线',
		'left_storage': 4096,
		'electric_percent': 80,
		'network_signal_strength': 4
	})
	print('Inserted id:', sid)
	print('Listing devices:')
	for d in list_devices():
		print(d['hardware_id'], d['hotel'], d['location'])

"""
SQLite 数据库模块
用于设备和任务数据的持久化存储
"""
from .sqllite_device import (
    init_db,
    insert_device,
    get_device,
    get_device_by_client_id,
    get_client_id_by_hardware_id,
    list_devices,
    update_device,
    delete_device
)

from .sqllite_task import (
    init_task_table,
    create_task,
    get_task_by_requestid,
    list_tasks,
    update_task,
    delete_task
)

__all__ = [
    # Device functions
    'init_db',
    'insert_device',
    'get_device',
    'get_device_by_client_id',
    'get_client_id_by_hardware_id',
    'list_devices',
    'update_device',
    'delete_device',
    
    # Task functions
    'init_task_table',
    'create_task',
    'get_task_by_requestid',
    'list_tasks',
    'update_task',
    'delete_task'
]


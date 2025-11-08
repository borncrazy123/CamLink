"""
设备状态管理模块
用于存储和管理摄像头设备的状态信息
"""
import json
import threading
from datetime import datetime
from typing import Dict, Optional

class DeviceStatusManager:
    """设备状态管理器，线程安全"""
    
    def __init__(self):
        self._statuses: Dict[str, dict] = {}
        self._lock = threading.Lock()
    
    def update_status(self, camera_id: str, status_data: dict):
        """
        更新设备状态
        
        Args:
            camera_id: 摄像头ID
            status_data: 状态数据字典，包含：
                - status: 在线状态 (online/offline)
                - run_state: 运行状态 (recording/stopped)
                - left_storage: 剩余容量 (GB)
                - electric_percent: 电量百分比 (0-1)
                - network_signal_strength: 网络信号强度 (dBm)
                - request_id: 请求ID（可选）
        """
        with self._lock:
            if camera_id not in self._statuses:
                self._statuses[camera_id] = {}
            
            # 更新状态数据
            self._statuses[camera_id].update({
                'status': status_data.get('status', 'unknown'),
                'run_state': status_data.get('run_state', 'unknown'),
                'left_storage': status_data.get('left_storage', 0),
                'electric_percent': status_data.get('electric_percent', '0'),
                'network_signal_strength': status_data.get('network_signal_strength', 0),
                'last_update': datetime.now().isoformat(),
                'request_id': status_data.get('request_id', '')
            })
    
    def get_status(self, camera_id: str) -> Optional[dict]:
        """
        获取设备状态
        
        Args:
            camera_id: 摄像头ID
            
        Returns:
            设备状态字典，如果不存在返回None
        """
        with self._lock:
            return self._statuses.get(camera_id, None)
    
    def get_all_statuses(self) -> Dict[str, dict]:
        """
        获取所有设备状态
        
        Returns:
            所有设备状态的字典
        """
        with self._lock:
            return self._statuses.copy()
    
    def get_status_list(self) -> list:
        """
        获取所有设备状态列表
        
        Returns:
            设备状态列表，每个元素包含camera_id和状态信息
        """
        with self._lock:
            return [
                {'camera_id': camera_id, **status}
                for camera_id, status in self._statuses.items()
            ]

# 全局单例
device_status_manager = DeviceStatusManager()


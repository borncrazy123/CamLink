"""
命令响应管理模块
用于存储和管理摄像头命令的响应结果
"""
import threading
from datetime import datetime
from typing import Dict, Optional

class CommandResponseManager:
    """命令响应管理器，线程安全"""
    
    def __init__(self):
        self._responses: Dict[str, dict] = {}
        self._lock = threading.Lock()
    
    def store_response(self, request_id: str, camera_id: str, response_data: dict):
        """
        存储命令响应
        
        Args:
            request_id: 请求ID
            camera_id: 摄像头ID
            response_data: 响应数据字典，包含：
                - result: 结果 (success/failed)
                - error_code: 错误码
                - error_msg: 错误信息（可选）
        """
        with self._lock:
            self._responses[request_id] = {
                'camera_id': camera_id,
                'result': response_data.get('result', 'unknown'),
                'error_code': response_data.get('error_code', -1),
                'error_msg': response_data.get('error_msg', ''),
                'timestamp': datetime.now().isoformat(),
                'raw_data': response_data
            }
    
    def get_response(self, request_id: str) -> Optional[dict]:
        """
        获取命令响应
        
        Args:
            request_id: 请求ID
            
        Returns:
            响应字典，如果不存在返回None
        """
        with self._lock:
            return self._responses.get(request_id, None)
    
    def get_camera_responses(self, camera_id: str) -> list:
        """
        获取指定摄像头的所有命令响应
        
        Args:
            camera_id: 摄像头ID
            
        Returns:
            响应列表
        """
        with self._lock:
            return [
                {'request_id': req_id, **resp}
                for req_id, resp in self._responses.items()
                if resp.get('camera_id') == camera_id
            ]
    
    def clear_response(self, request_id: str):
        """清除指定的命令响应"""
        with self._lock:
            if request_id in self._responses:
                del self._responses[request_id]
    
    def clear_old_responses(self, max_age_seconds: int = 3600):
        """
        清除旧的响应记录
        
        Args:
            max_age_seconds: 最大保留时间（秒），默认1小时
        """
        from datetime import datetime, timedelta
        with self._lock:
            current_time = datetime.now()
            expired_keys = []
            
            for req_id, resp in self._responses.items():
                timestamp = datetime.fromisoformat(resp['timestamp'])
                if (current_time - timestamp).total_seconds() > max_age_seconds:
                    expired_keys.append(req_id)
            
            for key in expired_keys:
                del self._responses[key]
            
            if expired_keys:
                print(f"Cleared {len(expired_keys)} expired command responses")

# 全局单例
command_response_manager = CommandResponseManager()


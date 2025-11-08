"""
视频管理模块
用于存储和管理视频列表和上传进度
"""
import threading
from datetime import datetime
from typing import Dict, Optional, List

class VideoListManager:
    """视频列表管理器，线程安全"""
    
    def __init__(self):
        self._video_lists: Dict[str, dict] = {}  # key: request_id, value: video_list_data
        self._camera_videos: Dict[str, dict] = {}  # key: camera_id, value: latest video list
        self._lock = threading.Lock()
    
    def store_video_list(self, request_id: str, camera_id: str, videos: list):
        """
        存储视频列表响应
        
        Args:
            request_id: 请求ID
            camera_id: 摄像头ID
            videos: 视频列表，每个元素包含 file_name, start_time, duration, size
        """
        with self._lock:
            data = {
                'camera_id': camera_id,
                'videos': videos,
                'count': len(videos),
                'timestamp': datetime.now().isoformat()
            }
            self._video_lists[request_id] = data
            self._camera_videos[camera_id] = data
    
    def get_video_list(self, request_id: str) -> Optional[dict]:
        """
        根据请求ID获取视频列表
        
        Args:
            request_id: 请求ID
            
        Returns:
            视频列表数据，如果不存在返回None
        """
        with self._lock:
            return self._video_lists.get(request_id, None)
    
    def get_camera_latest_videos(self, camera_id: str) -> Optional[dict]:
        """
        获取指定摄像头的最新视频列表
        
        Args:
            camera_id: 摄像头ID
            
        Returns:
            最新的视频列表数据
        """
        with self._lock:
            return self._camera_videos.get(camera_id, None)


class UploadProgressManager:
    """上传进度管理器，线程安全"""
    
    def __init__(self):
        # 存储每个摄像头的上传进度
        # key: camera_id, value: {file_name: progress, ...}
        self._upload_progress: Dict[str, Dict[str, float]] = {}
        # 存储历史上传任务记录
        # key: request_id, value: {camera_id, file_list, status, ...}
        self._upload_tasks: Dict[str, dict] = {}
        self._lock = threading.Lock()
    
    def create_upload_task(self, request_id: str, camera_id: str, file_name_list: list, success: bool):
        """
        创建上传任务记录
        
        Args:
            request_id: 请求ID
            camera_id: 摄像头ID
            file_name_list: 文件名列表
            success: 设备是否接受任务
        """
        with self._lock:
            self._upload_tasks[request_id] = {
                'camera_id': camera_id,
                'file_name_list': file_name_list,
                'success': success,
                'created_at': datetime.now().isoformat()
            }
    
    def update_progress(self, camera_id: str, file_progress: dict, request_id: str = None):
        """
        更新上传进度
        
        Args:
            camera_id: 摄像头ID
            file_progress: 文件进度字典，格式: {file_name: progress, ...}
            request_id: 请求ID（可选）
        """
        with self._lock:
            if camera_id not in self._upload_progress:
                self._upload_progress[camera_id] = {}
            
            # 更新每个文件的进度
            for file_name, progress in file_progress.items():
                self._upload_progress[camera_id][file_name] = progress
            
            # 移除已完成的文件（进度=1.0）
            completed_files = [
                fname for fname, prog in self._upload_progress[camera_id].items()
                if prog >= 1.0
            ]
            
            # 记录完成信息但保留一段时间
            if completed_files:
                print(f"✅ 文件上传完成: {completed_files}")
    
    def get_camera_progress(self, camera_id: str) -> Dict[str, float]:
        """
        获取指定摄像头的所有上传进度
        
        Args:
            camera_id: 摄像头ID
            
        Returns:
            上传进度字典
        """
        with self._lock:
            return self._upload_progress.get(camera_id, {}).copy()
    
    def get_file_progress(self, camera_id: str, file_name: str) -> Optional[float]:
        """
        获取指定文件的上传进度
        
        Args:
            camera_id: 摄像头ID
            file_name: 文件名
            
        Returns:
            上传进度（0.0-1.0），如果不存在返回None
        """
        with self._lock:
            return self._upload_progress.get(camera_id, {}).get(file_name, None)
    
    def get_upload_task(self, request_id: str) -> Optional[dict]:
        """
        获取上传任务信息
        
        Args:
            request_id: 请求ID
            
        Returns:
            任务信息字典
        """
        with self._lock:
            return self._upload_tasks.get(request_id, None)
    
    def clear_completed_files(self, camera_id: str):
        """
        清除已完成的文件进度
        
        Args:
            camera_id: 摄像头ID
        """
        with self._lock:
            if camera_id in self._upload_progress:
                self._upload_progress[camera_id] = {
                    fname: prog for fname, prog in self._upload_progress[camera_id].items()
                    if prog < 1.0
                }


# 全局单例
video_list_manager = VideoListManager()
upload_progress_manager = UploadProgressManager()


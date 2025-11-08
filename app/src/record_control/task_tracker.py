"""
任务跟踪器模块
负责在MQTT命令生命周期中记录和更新task表
"""
from datetime import datetime
from app.src.sqllite import create_task, update_task


def create_command_task(client_id: str, request_id: str, request_type: str, description: str = None) -> int:
    """
    创建命令任务记录
    
    Args:
        client_id: 摄像头client_id
        request_id: 请求ID
        request_type: 请求类型 (start_record/stop_record/list_videos/upload_file/get_upload_status)
        description: 操作描述
        
    Returns:
        task_id: 创建的任务ID
    """
    # 操作类型的中文描述映射
    type_desc_map = {
        'start_record': '启动录制',
        'stop_record': '停止录制',
        'list_videos': '查询视频列表',
        'upload_file': '上传文件',
        'get_upload_status': '查询上传进度',
        'get_status': '获取设备状态'
    }
    
    if description is None:
        description = f"{type_desc_map.get(request_type, '未知操作')}命令已下发"
    
    task_data = {
        'clientid': client_id,
        'requestid': request_id,
        'requesttype': request_type,
        'state': 'calling',  # 初始状态：调用中
        'description': description,
        'updated_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    }
    
    try:
        task_id = create_task(task_data)
        print(f"✅ 创建任务记录: task_id={task_id}, request_id={request_id}, type={request_type}")
        return task_id
    except Exception as e:
        print(f"❌ 创建任务记录失败: {e}")
        return -1


def update_command_task_success(request_id: str, description: str = None, result_data: dict = None) -> bool:
    """
    更新任务状态为成功
    
    Args:
        request_id: 请求ID
        description: 成功描述
        result_data: 响应数据（可选，用于生成更详细的描述）
        
    Returns:
        是否更新成功
    """
    if description is None:
        description = "命令执行成功"
    
    # 如果有result_data，可以生成更详细的描述
    if result_data:
        if 'videos' in result_data:
            video_count = len(result_data.get('videos', []))
            description = f"查询成功，找到 {video_count} 个视频文件"
        elif 'file_list_upload_progress' in result_data:
            progress_data = result_data.get('file_list_upload_progress', {})
            description = f"获取上传进度成功，{len(progress_data)} 个文件"
    
    patch = {
        'state': 'success',
        'description': description,
        'updated_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    }
    
    try:
        rows_updated = update_task(request_id, patch)
        if rows_updated > 0:
            print(f"✅ 更新任务状态为成功: request_id={request_id}")
            return True
        else:
            print(f"⚠️  未找到对应的任务记录: request_id={request_id}")
            return False
    except Exception as e:
        print(f"❌ 更新任务状态失败: {e}")
        return False


def update_command_task_failed(request_id: str, error_msg: str = None, error_code: int = None) -> bool:
    """
    更新任务状态为失败
    
    Args:
        request_id: 请求ID
        error_msg: 错误信息
        error_code: 错误代码
        
    Returns:
        是否更新成功
    """
    if error_msg is None:
        error_msg = "命令执行失败"
    
    if error_code is not None:
        description = f"执行失败 (错误码: {error_code}): {error_msg}"
    else:
        description = f"执行失败: {error_msg}"
    
    patch = {
        'state': 'failed',
        'description': description,
        'updated_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    }
    
    try:
        rows_updated = update_task(request_id, patch)
        if rows_updated > 0:
            print(f"✅ 更新任务状态为失败: request_id={request_id}, error={error_msg}")
            return True
        else:
            print(f"⚠️  未找到对应的任务记录: request_id={request_id}")
            return False
    except Exception as e:
        print(f"❌ 更新任务状态失败: {e}")
        return False


def update_command_task_description(request_id: str, description: str) -> bool:
    """
    只更新任务的描述信息（不改变状态）
    
    Args:
        request_id: 请求ID
        description: 新的描述信息
        
    Returns:
        是否更新成功
    """
    patch = {
        'description': description,
        'updated_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    }
    
    try:
        rows_updated = update_task(request_id, patch)
        return rows_updated > 0
    except Exception as e:
        print(f"❌ 更新任务描述失败: {e}")
        return False


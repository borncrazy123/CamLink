"""
状态监听器模块
用于监听摄像头设备的状态消息（响应和主动上报）
"""
from paho.mqtt import client as mqtt_client
import random
import time
import os
import threading
import json
import re
from datetime import datetime
from .device_status import device_status_manager
from app.src.record_control import (
    command_response_manager,
    update_command_task_success,
    update_command_task_failed
)
from app.src.video_manage import video_list_manager, upload_progress_manager
from app.src.sqllite import update_device, get_device_by_client_id, get_task_by_requestid

def update_device_status_to_db(camera_id: str, status_data: dict):
    """
    将设备状态同步更新到数据库
    
    Args:
        camera_id: 摄像头ID (对应数据库的hardware_id)
        status_data: 状态数据字典
    """
    try:
        # 构建数据库更新字段
        db_patch = {
            'last_online': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        
        # 状态映射：online -> 在线，offline -> 离线
        if 'status' in status_data:
            status_value = status_data['status']
            if status_value == 'online':
                db_patch['status'] = '在线'
            elif status_value == 'offline':
                db_patch['status'] = '离线'
            else:
                db_patch['status'] = status_value
        
        # 运行状态
        if 'run_state' in status_data:
            db_patch['run_state'] = status_data['run_state']
        
        # 剩余容量
        if 'left_storage' in status_data:
            db_patch['left_storage'] = int(status_data['left_storage'])
        
        # 电量百分比（从0-1小数转换为0-100整数）
        if 'electric_percent' in status_data:
            electric = status_data['electric_percent']
            if isinstance(electric, str):
                electric = float(electric)
            db_patch['electric_percent'] = int(electric * 100)
        
        # 网络信号强度
        if 'network_signal_strength' in status_data:
            db_patch['network_signal_strength'] = int(status_data['network_signal_strength'])
        
        # 更新数据库
        rows_updated = update_device(camera_id, db_patch)
        if rows_updated > 0:
            print(f"✅ 已同步设备状态到数据库: {camera_id}")
        else:
            print(f"⚠️  设备在数据库中不存在，无法更新: {camera_id}")
    
    except Exception as e:
        print(f"❌ 更新数据库失败 ({camera_id}): {e}")
        import traceback
        traceback.print_exc()


def create_status_listener():
    """
    创建并启动MQTT状态监听器
    监听三个主题：
    1. camera/+/resp - 设备响应消息 (QoS=1)
    2. camera/+/state - 设备主动上报状态 (QoS=0)
    3. camera/+/upload_file_status - 设备主动上报上传进度 (QoS=0)
    """
    print("------ 创建摄像头状态监听器 ------")
    broker = '121.36.170.241'
    port = 1883
    # 订阅摄像头响应、状态上报和上传进度主题
    topics = [
        ('camera/+/resp', 1),              # 设备响应（云端拉取后的回复）
        ('camera/+/state', 0),             # 设备主动上报状态
        ('camera/+/upload_file_status', 0) # 设备主动上报上传进度
    ]
    client_id = f'python-mqtt-status-listener-{random.randint(0, 1000)}'
    # MQTT broker 鉴权
    username = 'camlink'
    password = 'camlink'

    def on_connect(client, userdata, flags, rc):
        """连接成功回调"""
        if rc == 0:
            print("✅ 状态监听器已连接到 MQTT Broker!")
            client.subscribe(topics)
            print(f"📡 已订阅主题: {[t[0] for t in topics]}")
        else:
            print(f"❌ 连接失败, 返回码: {rc}")

    def on_message(client, userdata, msg):
        """
        处理接收到的MQTT消息
        
        消息来源：
        - camera/<camera_id>/resp: 云端主动拉取后设备的响应（状态查询或命令响应）
        - camera/<camera_id>/state: 设备主动上报的状态
        - camera/<camera_id>/upload_file_status: 设备主动上报上传进度
        """
        try:
            topic_str = msg.topic
            payload_str = msg.payload.decode('utf-8')
            
            print(f"[消息监听] 收到消息 - Topic: {topic_str}")
            print(f"[消息监听] 消息内容: {payload_str}")
            
            # 从主题中提取client_id和消息类型
            # 主题格式: camera/<client_id>/resp 或 camera/<client_id>/state 或 camera/<client_id>/upload_file_status
            # 注意：topic中的ID是client_id，不是hardware_id
            match = re.match(r'camera/([^/]+)/(resp|state|upload_file_status)', topic_str)
            if not match:
                print(f"⚠️  无效的主题格式: {topic_str}")
                return
            
            client_id = match.group(1)  # 从topic获取client_id
            message_type = match.group(2)  # 'resp' 或 'state' 或 'upload_file_status'
            
            # 通过client_id查找对应的设备，获取hardware_id
            device = get_device_by_client_id(client_id)
            if not device:
                print(f"⚠️  未找到对应的设备 (client_id: {client_id})")
                return
            
            camera_id = device['hardware_id']  # 使用hardware_id作为内部标识
            print(f"📡 设备映射: client_id={client_id} → hardware_id={camera_id}")
            
            # 解析JSON消息
            try:
                data = json.loads(payload_str)
            except json.JSONDecodeError as e:
                print(f"❌ JSON解析失败: {e}")
                return
            
            # 根据消息类型和内容分发处理
            if message_type == 'upload_file_status':
                # 处理上传进度消息
                handle_upload_progress(camera_id, data)
            elif 'videos' in data:
                # 视频列表响应（list_videos命令的响应）
                handle_video_list_response(camera_id, data)
            elif 'file_list_upload_progress' in data:
                # 上传进度查询响应（get_upload_status命令的响应）
                handle_upload_status_response(camera_id, data)
            elif 'result' in data:
                # 命令响应消息（包含result字段，如start_record, stop_record, upload_file的响应）
                request_id = data.get('request_id')
                if request_id:
                    command_response_manager.store_response(request_id, camera_id, data)
                    print(f"✅ 已存储命令响应 (camera: {camera_id}, request: {request_id}, result: {data.get('result')})")
                    
                    # 更新task状态
                    result = data.get('result')
                    error_code = data.get('error_code')
                    
                    if result == 'success':
                        update_command_task_success(request_id)
                        
                        # 🔥 当命令成功执行（error_code=0）时，根据命令类型自动更新 run_state
                        if error_code == 0:
                            # 从tasks表查询命令类型
                            task = get_task_by_requestid(request_id)
                            if task:
                                request_type = task.get('requesttype')
                                
                                # 根据命令类型推断设备运行状态
                                new_run_state = None
                                if request_type == 'start_record':
                                    new_run_state = 'recording'
                                    print(f"🎬 开始录制命令成功，更新 run_state = recording")
                                elif request_type == 'stop_record':
                                    new_run_state = 'stopped'
                                    print(f"⏹️  停止录制命令成功，更新 run_state = stopped")
                                
                                # 更新设备运行状态
                                if new_run_state:
                                    status_update = {
                                        'run_state': new_run_state,
                                        'status': 'online'  # 既然能响应命令，说明设备在线
                                    }
                                    device_status_manager.update_status(camera_id, status_update)
                                    update_device_status_to_db(camera_id, status_update)
                                    print(f"✅ 已自动更新设备运行状态: run_state={new_run_state}")
                    
                    elif result == 'failed':
                        error_msg = data.get('error_msg', '未知错误')
                        update_command_task_failed(request_id, error_msg, error_code)
                    
                    # 如果响应中明确包含 run_state 字段，优先使用（覆盖推断值）
                    if 'run_state' in data:
                        device_status_manager.update_status(camera_id, data)
                        update_device_status_to_db(camera_id, data)
                        print(f"✅ 使用响应中的 run_state: {data.get('run_state')}")
                else:
                    print(f"⚠️  命令响应缺少request_id")
            else:
                # 状态消息（状态查询响应或主动上报）
                # 1. 更新内存状态（实时查询使用）
                device_status_manager.update_status(camera_id, data)
                print(f"✅ 已更新摄像头 {camera_id} 内存状态 (来源: {message_type})")
                
                # 2. 同步更新数据库状态（持久化）
                update_device_status_to_db(camera_id, data)
            
        except Exception as e:
            print(f"❌ 处理MQTT消息时出错: {e}")
            import traceback
            traceback.print_exc()
    
    def handle_video_list_response(camera_id: str, data: dict):
        """处理视频列表响应"""
        request_id = data.get('request_id')
        videos = data.get('videos', [])
        if request_id:
            video_list_manager.store_video_list(request_id, camera_id, videos)
            print(f"✅ 已存储视频列表 (camera: {camera_id}, request: {request_id}, count: {len(videos)})")
            
            # 更新task状态为成功
            update_command_task_success(request_id, result_data=data)
        else:
            print(f"⚠️  视频列表响应缺少request_id")
    
    def handle_upload_progress(camera_id: str, data: dict):
        """处理上传进度消息（设备主动上报）"""
        request_id = data.get('request_id')
        file_progress = data.get('file_upload_progress', {})
        if file_progress:
            upload_progress_manager.update_progress(camera_id, file_progress, request_id)
            print(f"✅ 已更新上传进度 (camera: {camera_id}): {file_progress}")
        else:
            print(f"⚠️  上传进度消息缺少file_upload_progress字段")
    
    def handle_upload_status_response(camera_id: str, data: dict):
        """处理上传进度查询响应"""
        request_id = data.get('request_id')
        file_progress = data.get('file_list_upload_progress', {})
        if request_id and file_progress:
            upload_progress_manager.update_progress(camera_id, file_progress, request_id)
            print(f"✅ 已更新上传进度 (camera: {camera_id}, request: {request_id}): {file_progress}")
            
            # 更新task状态为成功
            update_command_task_success(request_id, result_data=data)
        elif not file_progress:
            print(f"⚠️  上传进度响应缺少file_list_upload_progress字段")

    # 创建MQTT客户端
    client = mqtt_client.Client(client_id=client_id)
    print(f"🔧 MQTT客户端已创建: {client_id}")
    client.username_pw_set(username, password)
    client.on_connect = on_connect
    client.on_message = on_message

    # 连接循环，支持自动重连
    while True:
        try:
            print(f"🔄 正在连接 MQTT Broker: {broker}:{port}")
            client.connect(broker, port)
            client.loop_forever()
        except Exception as e:
            print(f"❌ MQTT 连接失败，5秒后重试: {e}")
            time.sleep(5)
        finally:
            print("🔌 断开 MQTT Broker 连接...")
            try:
                client.disconnect()
            except:
                pass


"""
MQTT发布器模块
用于向摄像头设备发送命令
"""
from paho.mqtt import client as mqtt_client
import json
import random
import time
import threading
from app.src.sqllite import get_client_id_by_hardware_id
from app.src.record_control import create_command_task

class MQTTPublisher:
    """MQTT发布器，用于发送命令到设备"""
    
    def __init__(self, broker='121.36.170.241', port=1883, username='camlink', password='camlink'):
        self.broker = broker
        self.port = port
        self.username = username
        self.password = password
        self.client_id = f'python-mqtt-publisher-{random.randint(0, 10000)}'
        self.client = None
        self._lock = threading.Lock()
        self._connected = False
    
    def connect(self):
        """连接到MQTT broker"""
        if self._connected and self.client is not None:
            return True
        
        try:
            self.client = mqtt_client.Client(client_id=self.client_id)
            self.client.username_pw_set(self.username, self.password)
            
            def on_connect(client, userdata, flags, rc):
                if rc == 0:
                    self._connected = True
                    print(f"MQTT Publisher connected successfully!")
                else:
                    self._connected = False
                    print(f"MQTT Publisher failed to connect, return code {rc}")
            
            def on_disconnect(client, userdata, rc):
                self._connected = False
                print(f"MQTT Publisher disconnected, return code {rc}")
            
            self.client.on_connect = on_connect
            self.client.on_disconnect = on_disconnect
            
            self.client.connect(self.broker, self.port, keepalive=60)
            self.client.loop_start()
            
            # 等待连接建立
            timeout = 5
            start_time = time.time()
            while not self._connected and (time.time() - start_time) < timeout:
                time.sleep(0.1)
            
            return self._connected
        except Exception as e:
            print(f"MQTT Publisher connection error: {e}")
            self._connected = False
            return False
    
    def publish_command(self, camera_id: str, action: str, request_id: str = None) -> bool:
        """
        发布命令到设备
        
        Args:
            camera_id: 摄像头ID (hardware_id)
            action: 操作类型，如 'get_status'
            request_id: 请求ID，如果不提供则自动生成
            
        Returns:
            是否发布成功
        """
        if not self._connected:
            if not self.connect():
                return False
        
        # 将hardware_id转换为client_id（MQTT topic使用client_id）
        client_id = get_client_id_by_hardware_id(camera_id)
        if not client_id:
            print(f"❌ 未找到设备的client_id (hardware_id: {camera_id})")
            return False
        
        if request_id is None:
            request_id = f"req_{int(time.time() * 1000)}_{random.randint(1000, 9999)}"
        
        # MQTT topic使用client_id，不是hardware_id
        topic = f"camera/{client_id}/cmd"
        payload = {
            "action": action,
            "request_id": request_id
        }
        
        try:
            with self._lock:
                result = self.client.publish(topic, json.dumps(payload), qos=1, retain=False)
                if result.rc == 0:
                    print(f"✅ 发送命令成功 - hardware_id: {camera_id}, client_id: {client_id}")
                    print(f"   Topic: {topic}, Payload: {payload}")
                    return True
                else:
                    print(f"❌ 发送命令失败 - Topic: {topic}, return code: {result.rc}")
                    return False
        except Exception as e:
            print(f"❌ 发送命令异常: {e}")
            return False
    
    def get_status(self, camera_id: str, request_id: str = None) -> bool:
        """
        获取设备状态
        
        Args:
            camera_id: 摄像头ID
            request_id: 请求ID，如果不提供则自动生成
            
        Returns:
            是否发送成功
        """
        return self.publish_command(camera_id, "get_status", request_id)
    
    def start_record(self, camera_id: str, pre_name: str, request_id: str = None) -> tuple:
        """
        启动录制
        
        Args:
            camera_id: 摄像头ID (hardware_id)
            pre_name: 业务标识参数，用于标识录制场景（如"702房间"、"会议室A"等）
                     将作为文件名的一部分，格式: {时间戳}_{pre_name}.mp4
            request_id: 请求ID，如果不提供则自动生成
            
        Returns:
            (是否发送成功, request_id)
        """
        if not self._connected:
            if not self.connect():
                return (False, None)
        
        # 将hardware_id转换为client_id（MQTT topic使用client_id）
        client_id = get_client_id_by_hardware_id(camera_id)
        if not client_id:
            print(f"❌ 未找到设备的client_id (hardware_id: {camera_id})")
            return (False, None)
        
        if request_id is None:
            request_id = f"req_{int(time.time() * 1000)}_{random.randint(1000, 9999)}"
        
        # MQTT topic使用client_id
        topic = f"camera/{client_id}/cmd"
        payload = {
            "action": "start_record",
            "request_id": request_id,
            "pre_name": pre_name
        }
        
        try:
            with self._lock:
                result = self.client.publish(topic, json.dumps(payload), qos=1, retain=False)
                if result.rc == 0:
                    print(f"✅ 发送开始录制命令 - hardware_id: {camera_id}, client_id: {client_id}")
                    print(f"   Topic: {topic}, Payload: {payload}")
                    
                    # 创建任务记录
                    create_command_task(
                        client_id=client_id,
                        request_id=request_id,
                        request_type='start_record',
                        description=f'启动录制命令已下发 (场景: {pre_name})'
                    )
                    
                    return (True, request_id)
                else:
                    print(f"❌ 发送开始录制命令失败 - Topic: {topic}, return code: {result.rc}")
                    return (False, request_id)
        except Exception as e:
            print(f"❌ 发送开始录制命令异常: {e}")
            return (False, request_id)
    
    def stop_record(self, camera_id: str, request_id: str = None) -> tuple:
        """
        停止录制
        
        Args:
            camera_id: 摄像头ID (hardware_id)
            request_id: 请求ID，如果不提供则自动生成
            
        Returns:
            (是否发送成功, request_id)
        """
        if not self._connected:
            if not self.connect():
                return (False, None)
        
        # 将hardware_id转换为client_id（MQTT topic使用client_id）
        client_id = get_client_id_by_hardware_id(camera_id)
        if not client_id:
            print(f"❌ 未找到设备的client_id (hardware_id: {camera_id})")
            return (False, None)
        
        if request_id is None:
            request_id = f"req_{int(time.time() * 1000)}_{random.randint(1000, 9999)}"
        
        # MQTT topic使用client_id
        topic = f"camera/{client_id}/cmd"
        payload = {
            "action": "stop_record",
            "request_id": request_id
        }
        
        try:
            with self._lock:
                result = self.client.publish(topic, json.dumps(payload), qos=1, retain=False)
                if result.rc == 0:
                    print(f"✅ 发送停止录制命令 - hardware_id: {camera_id}, client_id: {client_id}")
                    print(f"   Topic: {topic}, Payload: {payload}")
                    
                    # 创建任务记录
                    create_command_task(
                        client_id=client_id,
                        request_id=request_id,
                        request_type='stop_record',
                        description='停止录制命令已下发'
                    )
                    
                    return (True, request_id)
                else:
                    print(f"❌ 发送停止录制命令失败 - Topic: {topic}, return code: {result.rc}")
                    return (False, request_id)
        except Exception as e:
            print(f"❌ 发送停止录制命令异常: {e}")
            return (False, request_id)
    
    def list_videos(self, camera_id: str, start_time: str = None, end_time: str = None, 
                   min_size: int = 0, max_size: int = None, request_id: str = None) -> tuple:
        """
        查询视频列表
        
        Args:
            camera_id: 摄像头ID (hardware_id)
            start_time: 开始时间（ISO格式，如"2025-10-01T00:00:00Z"）
            end_time: 结束时间（ISO格式）
            min_size: 最小文件大小（字节）
            max_size: 最大文件大小（字节）
            request_id: 请求ID，如果不提供则自动生成
            
        Returns:
            (是否发送成功, request_id)
        """
        if not self._connected:
            if not self.connect():
                return (False, None)
        
        # 将hardware_id转换为client_id（MQTT topic使用client_id）
        client_id = get_client_id_by_hardware_id(camera_id)
        if not client_id:
            print(f"❌ 未找到设备的client_id (hardware_id: {camera_id})")
            return (False, None)
        
        if request_id is None:
            request_id = f"req_{int(time.time() * 1000)}_{random.randint(1000, 9999)}"
        
        # MQTT topic使用client_id
        topic = f"camera/{client_id}/cmd"
        payload = {
            "action": "list_videos",
            "request_id": request_id,
            "params": {
                "min_size": min_size
            }
        }
        
        # 添加可选参数
        if start_time:
            payload["params"]["start_time"] = start_time
        if end_time:
            payload["params"]["end_time"] = end_time
        if max_size is not None:
            payload["params"]["max_size"] = max_size
        
        try:
            with self._lock:
                result = self.client.publish(topic, json.dumps(payload), qos=1, retain=False)
                if result.rc == 0:
                    print(f"✅ 发送查询视频列表命令 - hardware_id: {camera_id}, client_id: {client_id}")
                    print(f"   Topic: {topic}, Payload: {payload}")
                    
                    # 创建任务记录
                    create_command_task(
                        client_id=client_id,
                        request_id=request_id,
                        request_type='list_videos',
                        description='查询视频列表命令已下发'
                    )
                    
                    return (True, request_id)
                else:
                    print(f"❌ 发送查询视频列表命令失败 - Topic: {topic}, return code: {result.rc}")
                    return (False, request_id)
        except Exception as e:
            print(f"❌ 发送查询视频列表命令异常: {e}")
            return (False, request_id)
    
    def upload_file(self, camera_id: str, file_name_list: list, request_id: str = None) -> tuple:
        """
        请求设备上传指定的视频文件
        
        Args:
            camera_id: 摄像头ID (hardware_id)
            file_name_list: 要上传的文件名列表，如 ["vid_001", "vid_002"]
            request_id: 请求ID，如果不提供则自动生成
            
        Returns:
            (是否发送成功, request_id)
        """
        if not self._connected:
            if not self.connect():
                return (False, None)
        
        # 将hardware_id转换为client_id（MQTT topic使用client_id）
        client_id = get_client_id_by_hardware_id(camera_id)
        if not client_id:
            print(f"❌ 未找到设备的client_id (hardware_id: {camera_id})")
            return (False, None)
        
        if request_id is None:
            request_id = f"req_{int(time.time() * 1000)}_{random.randint(1000, 9999)}"
        
        # MQTT topic使用client_id
        topic = f"camera/{client_id}/cmd"
        payload = {
            "action": "upload_file",
            "request_id": request_id,
            "params": {
                "file_name_list": file_name_list
            }
        }
        
        try:
            with self._lock:
                result = self.client.publish(topic, json.dumps(payload), qos=1, retain=False)
                if result.rc == 0:
                    print(f"✅ 发送上传文件命令 - hardware_id: {camera_id}, client_id: {client_id}")
                    print(f"   Topic: {topic}, Payload: {payload}")
                    
                    # 创建任务记录
                    file_count = len(file_name_list)
                    create_command_task(
                        client_id=client_id,
                        request_id=request_id,
                        request_type='upload_file',
                        description=f'上传文件命令已下发 ({file_count}个文件)'
                    )
                    
                    return (True, request_id)
                else:
                    print(f"❌ 发送上传文件命令失败 - Topic: {topic}, return code: {result.rc}")
                    return (False, request_id)
        except Exception as e:
            print(f"❌ 发送上传文件命令异常: {e}")
            return (False, request_id)
    
    def get_upload_status(self, camera_id: str, file_name_list: list = None, request_id: str = None) -> tuple:
        """
        获取文件上传进度
        
        Args:
            camera_id: 摄像头ID (hardware_id)
            file_name_list: 要查询的文件名列表（可选）
            request_id: 请求ID，如果不提供则自动生成
            
        Returns:
            (是否发送成功, request_id)
        """
        if not self._connected:
            if not self.connect():
                return (False, None)
        
        # 将hardware_id转换为client_id（MQTT topic使用client_id）
        client_id = get_client_id_by_hardware_id(camera_id)
        if not client_id:
            print(f"❌ 未找到设备的client_id (hardware_id: {camera_id})")
            return (False, None)
        
        if request_id is None:
            request_id = f"req_{int(time.time() * 1000)}_{random.randint(1000, 9999)}"
        
        # MQTT topic使用client_id
        topic = f"camera/{client_id}/cmd"
        payload = {
            "action": "get_upload_status",
            "request_id": request_id,
            "params": {}
        }
        
        # 添加可选的文件列表参数
        if file_name_list:
            payload["params"]["file_name_list"] = file_name_list
        
        try:
            with self._lock:
                result = self.client.publish(topic, json.dumps(payload), qos=1, retain=False)
                if result.rc == 0:
                    print(f"✅ 发送获取上传状态命令 - hardware_id: {camera_id}, client_id: {client_id}")
                    print(f"   Topic: {topic}, Payload: {payload}")
                    
                    # 创建任务记录
                    create_command_task(
                        client_id=client_id,
                        request_id=request_id,
                        request_type='get_upload_status',
                        description='查询上传进度命令已下发'
                    )
                    
                    return (True, request_id)
                else:
                    print(f"❌ 发送获取上传状态命令失败 - Topic: {topic}, return code: {result.rc}")
                    return (False, request_id)
        except Exception as e:
            print(f"❌ 发送获取上传状态命令异常: {e}")
            return (False, request_id)
    
    def disconnect(self):
        """断开连接"""
        if self.client is not None:
            self.client.loop_stop()
            self.client.disconnect()
            self._connected = False

# 全局单例
mqtt_publisher = MQTTPublisher()


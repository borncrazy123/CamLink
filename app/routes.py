from flask import Blueprint, render_template, jsonify, request
import json
import requests
import hashlib
from requests.auth import HTTPBasicAuth
from app.src.monitor_cam import device_status_manager
from app.src.mqtt.mqtt_publisher import mqtt_publisher
from app.src.record_control import command_response_manager
from app.src.video_manage import video_list_manager, upload_progress_manager
from app.src.sqllite import list_devices, get_device, update_device, insert_device, list_tasks, get_client_id_by_hardware_id, delete_device
import sqlite3
from app.src.oss.oss_manager import getMultipartUploadPresignUrls, confirmCompleteMultipartUpload

main = Blueprint('main', __name__)

# ==================== 辅助函数 ====================

def convert_device_to_api_format(device_dict):
    """
    将数据库中的设备记录转换为API返回格式
    
    数据库字段 -> API字段映射：
    - hardware_id -> camera_id
    - status -> status (转换为 online/offline)
    - last_online -> last_update
    """
    # 状态转换：中文 -> 英文
    status_map = {
        '在线': 'online',
        '离线': 'offline',
        'online': 'online',
        'offline': 'offline'
    }
    
    return {
        'camera_id': device_dict.get('hardware_id', ''),
        'status': status_map.get(device_dict.get('status', 'offline'), 'offline'),
        'run_state': device_dict.get('run_state', 'stopped'),  # 默认为stopped
        'left_storage': device_dict.get('left_storage', 0),
        'electric_percent': device_dict.get('electric_percent', 0) / 100.0 if device_dict.get('electric_percent') else 0,  # 转换为0-1的小数
        'network_signal_strength': device_dict.get('network_signal_strength', 0),
        'last_update': device_dict.get('last_online', ''),
        # 额外字段供详情页使用
        'client_id': device_dict.get('client_id', ''),
        'hotel': device_dict.get('hotel', ''),
        'location': device_dict.get('location', ''),
        'wifi': device_dict.get('wifi', ''),
        'runtime': device_dict.get('runtime', ''),
        'firmware': device_dict.get('fw', 'v2.1.3')
    }

# ==================== 路由 ====================

@main.route('/')
def home():
    return render_template('device_manage.html')
    # return render_template('index.html')

@main.route('/camera_config')
def camera_config():
    return render_template('camera_config.html')


@main.route('/api/generate_config', methods=['POST'])
def generate_config():
    """Generate a configuration payload from form data and return it as JSON."""
    payload = {}
    if request.is_json:
        payload = request.get_json()
    else:
        payload = request.form.to_dict()

    hardware_id = payload.get('hardware_id')
    if not hardware_id:
        return jsonify({'ok': False, 'message': 'hardware_id is required'}), 400

    # generate client_id as CAM- + first 12 chars of md5(hardware_id)
    client_id = 'CAM-' + hashlib.md5(hardware_id.encode('utf-8')).hexdigest()[:12]

    config = {
        'hardware_id': hardware_id,
        'client_id': client_id,
        'hotel_name': payload.get('hotel_name'),
        'location': payload.get('location'),
        'wifi': {
            'ssid': payload.get('wifi_ssid'),
            'password': payload.get('wifi_password')
        }
    }

    # Persist to DB unless client asks for preview only
    hardware_id = payload.get('hardware_id')
    # prepare device row data
    device_row = {
        'hardware_id': hardware_id,
        'client_id': client_id,
        'hotel': payload.get('hotel_name'),
        'location': payload.get('location'),
        'wifi': payload.get('wifi_ssid'),
        'runtime': payload.get('runtime'),
        'fw': payload.get('fw'),
        'last_online': payload.get('last_online')
    }

    force = False
    # support force flag in JSON or form
    if 'force' in payload:
        v = payload.get('force')
        if isinstance(v, bool):
            force = v
        elif isinstance(v, str) and v.lower() in ('1', 'true', 'yes'):
            force = True
    print('-------->:',device_row)
    try:
        if force:
            # overwrite existing
            update_device(hardware_id, {k: v for k, v in device_row.items() if k != 'hardware_id' and v is not None})
        else:
            # try insert; will raise IntegrityError if exists
            insert_device(device_row)
    except sqlite3.IntegrityError:
        return jsonify({'ok': False, 'exists': True, 'message': 'hardware_id already exists'}), 409

    # Return pretty-printed JSON string
    return jsonify({'ok': True, 'config': json.dumps(config, ensure_ascii=False, indent=2)})

@main.route('/device_manage')
def device_manage():
    return render_template('device_manage.html')

@main.route('/hello')
def hello():
    return "Hello, World!"

@main.route('/v1/devices/register')
def register():
    # 模拟设备注册请求
    # {
    # # "client_id": "CLK_123456789",//最好用设备表面条码
    # # "device_secret": "a_very_long_and_secret_factory_key",//可以考虑去掉
    # # "model": "CAM-PRO-4K",//可以写死
    # # "firmware_version": "1.0.0" //设备自动读取本身的版本号
    # }

    # 模拟返回注册成功响应
    ret = {
        "result": "success",
        "data": {
            "client_id": "CLK_123456789",
            "mqtt_broker": {
                "host": "121.36.170.241",
                "port": 1883,
                "username": "camlink_c_1",
                "password": "camlink_c_1",
                "tls_enabled": False
            },
            "ota_info": {
                "download_url": "https://api.your-platform.com/v1/devices/upload_url",
                "firmware_version": "1.0.0",
                "update": "1" 
            }
        }
    }
    return ret

@main.route('/v1/devices/login')
def login():
    # 模拟设备登录请求
    # {
    #     "client_id": "CLK_123456789",
    #     "firmware_version": "1.0.0"
    # }

    # 模拟返回登录成功响应
    ret = {
        "result": "success",
        "data": {
            "client_id": "CLK_123456789",
            "mqtt_broker": {
                "host": "121.36.170.241",
                "port": 1883,
                "username": "camlink_c_1",
                "password": "camlink_c_1",
                "tls_enabled": False
            },
            "ota_info": {
                "download_url": "https://api.your-platform.com/v1/devices/upload_url",
                "firmware_version": "1.0.0",
                "update": "1" 
            }
        }
    }
    return ret

@main.route('/v1/devices/getMulUploadUrls', methods=['POST'])
def getMulUploadUrls():
    # 获取文件分片上传地址列表
    # {
    # "client_id": "CLK_123456789",
    # "fileName": "vid_001.mp4",
    # "partNumber": 2
    # }

    payload = {}
    if request.is_json:
        payload = request.get_json()
    else:
        payload = request.form.to_dict()

    clientId = payload.get('client_id')
    partNumber = payload.get('partNumber')
    fileName = payload.get('fileName')
    key = f"{clientId}/{fileName}"
    print("key for upload:", key)

    # 获取分片上传预签名URLs
    presignUrls = getMultipartUploadPresignUrls(bucket='camlink', key=key, part_number=partNumber)
    print("upload_id from getMultipartUploadPresignUrls():", presignUrls)
    upload_id = presignUrls["upload_id"]

    # 模拟返回登录成功响应
    ret = {
        "result": "success",
        "message": "",
        "data": {
            "uploadId": upload_id,
            "presignUrls": presignUrls["upload_parts"]
        }
    }

    return ret

@main.route('/v1/devices/confirmCmplMulUpload', methods=['POST'])
def confirmCmplMulUpload():
    # 获取文件分片上传完成校验
    # {
    #     "client_id": "CLK_123456789",
    #     "fileName": "vid_001.mp4",
    #     "uploadId": "DE304FF9AD8641E68FC9332E47113B50",
    #     "etagList": [{
    #         "partNumber": 1,
    #         "etag": "1EC0FCA281C9D4D4E1EFFA85972ACF14"
    #     }, {
    #         "partNumber": 2,
    #         "etag": "7F44980A40B0C1FB750ADB2F312E3C81"
    #     }]
    # }

    payload = {}
    if request.is_json:
        payload = request.get_json()
    else:
        payload = request.form.to_dict()    
    clientId = payload.get('client_id')
    fileName = payload.get('fileName')
    uploadId = payload.get('uploadId')
    etagList = payload.get('etagList')
    key = f"{clientId}/{fileName}"
    print("key for upload:", key)

    # 发送完成多部分上传请求
    confirmCompleteMultipartUpload(bucket='camlink', key=key, upload_id=uploadId, upload_parts=etagList) 

    # 模拟返回登录成功响应
    ret = {
        "result": "success",
        "message": ""
    }
    return ret

@main.route('/clients')
def client_list():

    # API 地址
    url = "http://121.36.170.241:18083/api/v4/clients/"

    # 认证信息
    auth = HTTPBasicAuth("admin", "public")

    # 发送 GET 请求
    try:
        response = requests.get(url, auth=auth, timeout=10)

        # 打印状态码和响应内容
        print("状态码:", response.status_code)

        if response.status_code == 200:
            data = response.json()
            print("连接的客户端：")
            print(data)
        else:
            print("响应内容：", response.text)

    except requests.exceptions.RequestException as e:
        print("请求失败:", e)


    return response.text


@main.route('/api/camera/<camera_id>/status', methods=['GET'])
def get_camera_status(camera_id):
    """
    获取摄像头状态
    
    Args:
        camera_id: 摄像头ID
        
    Returns:
        JSON格式的设备状态
    """
    status = device_status_manager.get_status(camera_id)
    if status:
        return jsonify({
            'success': True,
            'camera_id': camera_id,
            'data': status
        })
    else:
        return jsonify({
            'success': False,
            'camera_id': camera_id,
            'message': '设备状态不存在，可能设备尚未上报状态'
        }), 404


@main.route('/api/camera/<camera_id>/status/refresh', methods=['POST'])
def refresh_camera_status(camera_id):
    """
    主动获取摄像头状态（发送get_status命令）
    
    Args:
        camera_id: 摄像头ID
        
    Returns:
        JSON格式的响应
    """
    # 从请求中获取request_id（可选）
    request_id = None
    if request.is_json:
        data = request.get_json()
        request_id = data.get('request_id')
    
    # 发送获取状态命令
    success = mqtt_publisher.get_status(camera_id, request_id)
    
    if success:
        return jsonify({
            'success': True,
            'camera_id': camera_id,
            'message': '状态查询命令已发送，请稍后查询状态'
        })
    else:
        return jsonify({
            'success': False,
            'camera_id': camera_id,
            'message': '发送状态查询命令失败，请检查MQTT连接'
        }), 500


@main.route('/api/camera/status/all', methods=['GET'])
def get_all_camera_status():
    """
    获取所有摄像头状态
    
    Returns:
        JSON格式的所有设备状态列表
    """
    statuses = device_status_manager.get_all_statuses()
    return jsonify({
        'success': True,
        'count': len(statuses),
        'data': statuses
    })


@main.route('/api/camera/status/list', methods=['GET'])
def get_camera_status_list():
    """
    获取所有摄像头状态列表（从数据库读取）
    
    Returns:
        JSON格式的设备状态列表
    """
    try:
        # 从数据库获取设备列表
        db_devices = list_devices(limit=100)
        
        # 转换为API格式
        api_devices = [convert_device_to_api_format(device) for device in db_devices]
        
        # 可选：与内存中的实时状态合并（如果需要更实时的数据）
        # 这样可以获取到MQTT实时更新的状态
        memory_statuses = device_status_manager.get_all_statuses()
        for device in api_devices:
            camera_id = device['camera_id']
            if camera_id in memory_statuses:
                # 用内存中的实时状态覆盖数据库的状态
                memory_status = memory_statuses[camera_id]
                device['status'] = memory_status.get('status', device['status'])
                device['run_state'] = memory_status.get('run_state', device['run_state'])
                device['left_storage'] = memory_status.get('left_storage', device['left_storage'])
                device['electric_percent'] = memory_status.get('electric_percent', device['electric_percent'])
                device['network_signal_strength'] = memory_status.get('network_signal_strength', device['network_signal_strength'])
                device['last_update'] = memory_status.get('last_update', device['last_update'])
        
        return jsonify({
            'success': True,
            'count': len(api_devices),
            'data': api_devices
        })
    except Exception as e:
        print(f"Error fetching device list: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'message': f'获取设备列表失败: {str(e)}',
            'data': []
        }), 500


@main.route('/api/device/<camera_id>', methods=['DELETE'])
def delete_device_api(camera_id):
    """
    删除设备记录（通过 hardware_id）
    返回: { success: true } 或 404/500
    """
    try:
        # 使用 sqlite helper 删除
        removed = delete_device(camera_id)
        if removed and removed > 0:
            return jsonify({'success': True, 'message': f'设备 {camera_id} 已删除'})
        else:
            return jsonify({'success': False, 'message': f'未找到设备: {camera_id}'}), 404
    except Exception as e:
        print(f"❌ 删除设备失败: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'message': f'删除失败: {str(e)}'}), 500


# ==================== 录制控制接口 ====================

@main.route('/api/camera/<camera_id>/record/start', methods=['POST'])
def start_camera_record(camera_id):
    """
    启动摄像头录制
    
    Args:
        camera_id: 摄像头ID
        
    Request Body:
        {
            "pre_name": "702房间",        # 业务标识（如房间号、会议室等）
            "request_id": "optional"      # 可选的请求ID
        }
    
    Returns:
        JSON格式的响应
    
    说明:
        pre_name 用于标识本次录制的业务场景，会作为视频文件名的一部分
        最终文件名格式: {时间戳}_{pre_name}.mp4
        例如: 202510041122330001_702房间.mp4
    """
    if not request.is_json:
        return jsonify({
            'success': False,
            'message': '请求必须是JSON格式'
        }), 400
    
    data = request.get_json()
    pre_name = data.get('pre_name')
    
    if not pre_name:
        return jsonify({
            'success': False,
            'message': '缺少必需参数: pre_name'
        }), 400
    
    # 验证pre_name不为空且长度合理
    pre_name = str(pre_name).strip()
    if not pre_name or len(pre_name) > 100:
        return jsonify({
            'success': False,
            'message': 'pre_name不能为空且长度不能超过100个字符'
        }), 400
    
    # 可选：检查是否包含文件系统不安全字符（根据需要启用）
    # import re
    # if re.search(r'[<>:"/\\|?*]', pre_name):
    #     return jsonify({
    #         'success': False,
    #         'message': 'pre_name包含不安全字符'
    #     }), 400
    
    request_id = data.get('request_id')
    
    # 发送启动录制命令
    success, req_id = mqtt_publisher.start_record(camera_id, pre_name, request_id)
    
    if success:
        return jsonify({
            'success': True,
            'camera_id': camera_id,
            'request_id': req_id,
            'message': '录制启动命令已发送，请使用request_id查询结果'
        })
    else:
        return jsonify({
            'success': False,
            'camera_id': camera_id,
            'message': '发送录制启动命令失败，请检查MQTT连接'
        }), 500


@main.route('/api/camera/<camera_id>/record/stop', methods=['POST'])
def stop_camera_record(camera_id):
    """
    停止摄像头录制
    
    Args:
        camera_id: 摄像头ID
        
    Request Body (可选):
        {
            "request_id": "optional"  # 可选的请求ID
        }
    
    Returns:
        JSON格式的响应
    """
    request_id = None
    if request.is_json:
        data = request.get_json()
        request_id = data.get('request_id')
    
    # 发送停止录制命令
    success, req_id = mqtt_publisher.stop_record(camera_id, request_id)
    
    if success:
        return jsonify({
            'success': True,
            'camera_id': camera_id,
            'request_id': req_id,
            'message': '录制停止命令已发送，请使用request_id查询结果'
        })
    else:
        return jsonify({
            'success': False,
            'camera_id': camera_id,
            'message': '发送录制停止命令失败，请检查MQTT连接'
        }), 500


@main.route('/api/command/response/<request_id>', methods=['GET'])
def get_command_response(request_id):
    """
    查询命令响应结果
    
    Args:
        request_id: 请求ID
        
    Returns:
        JSON格式的命令响应
    """
    response = command_response_manager.get_response(request_id)
    
    if response:
        return jsonify({
            'success': True,
            'request_id': request_id,
            'data': response
        })
    else:
        return jsonify({
            'success': False,
            'request_id': request_id,
            'message': '未找到该请求的响应，可能设备尚未响应或request_id错误'
        }), 404


@main.route('/api/camera/<camera_id>/commands', methods=['GET'])
def get_camera_commands(camera_id):
    """
    获取指定摄像头的所有命令响应
    
    Args:
        camera_id: 摄像头ID
        
    Returns:
        JSON格式的命令响应列表
    """
    responses = command_response_manager.get_camera_responses(camera_id)
    return jsonify({
        'success': True,
        'camera_id': camera_id,
        'count': len(responses),
        'data': responses
    })


# ==================== 视频文件管理接口 ====================

@main.route('/api/camera/<camera_id>/videos/list', methods=['POST'])
def list_camera_videos(camera_id):
    """
    查询摄像头的视频列表
    
    Args:
        camera_id: 摄像头ID
        
    Request Body (可选):
        {
            "start_time": "2025-10-01T00:00:00Z",  # 开始时间
            "end_time": "2025-10-05T00:00:00Z",    # 结束时间
            "min_size": 0,                          # 最小文件大小（字节）
            "max_size": 500000000,                  # 最大文件大小（字节）
            "request_id": "optional"                # 可选的请求ID
        }
    
    Returns:
        JSON格式的响应，包含request_id用于后续查询结果
    """
    data = {}
    if request.is_json:
        data = request.get_json()
    
    start_time = data.get('start_time')
    end_time = data.get('end_time')
    min_size = data.get('min_size', 0)
    max_size = data.get('max_size')
    request_id = data.get('request_id')
    
    # 发送查询视频列表命令
    success, req_id = mqtt_publisher.list_videos(
        camera_id, start_time, end_time, min_size, max_size, request_id
    )
    
    if success:
        return jsonify({
            'success': True,
            'camera_id': camera_id,
            'request_id': req_id,
            'message': '视频列表查询命令已发送，请使用request_id查询结果'
        })
    else:
        return jsonify({
            'success': False,
            'camera_id': camera_id,
            'message': '发送视频列表查询命令失败，请检查MQTT连接'
        }), 500


@main.route('/api/videos/<request_id>', methods=['GET'])
def get_video_list_result(request_id):
    """
    根据request_id获取视频列表查询结果
    
    Args:
        request_id: 请求ID
        
    Returns:
        JSON格式的视频列表
    """
    video_list = video_list_manager.get_video_list(request_id)
    
    if video_list:
        return jsonify({
            'success': True,
            'request_id': request_id,
            'data': video_list
        })
    else:
        return jsonify({
            'success': False,
            'request_id': request_id,
            'message': '未找到视频列表，可能设备尚未响应或request_id错误'
        }), 404


@main.route('/api/camera/<camera_id>/videos/latest', methods=['GET'])
def get_camera_latest_videos(camera_id):
    """
    获取指定摄像头的最新视频列表
    
    Args:
        camera_id: 摄像头ID
        
    Returns:
        JSON格式的最新视频列表
    """
    video_list = video_list_manager.get_camera_latest_videos(camera_id)
    
    if video_list:
        return jsonify({
            'success': True,
            'camera_id': camera_id,
            'data': video_list
        })
    else:
        return jsonify({
            'success': False,
            'camera_id': camera_id,
            'message': '该摄像头暂无视频列表数据'
        }), 404


@main.route('/api/camera/<camera_id>/videos/upload', methods=['POST'])
def request_upload_videos(camera_id):
    """
    请求摄像头上传指定的视频文件
    
    Args:
        camera_id: 摄像头ID
        
    Request Body:
        {
            "file_name_list": ["vid_001", "vid_002"],  # 必需，要上传的文件名列表
            "request_id": "optional"                    # 可选的请求ID
        }
    
    Returns:
        JSON格式的响应
    """
    if not request.is_json:
        return jsonify({
            'success': False,
            'message': '请求必须是JSON格式'
        }), 400
    
    data = request.get_json()
    file_name_list = data.get('file_name_list')
    
    if not file_name_list or not isinstance(file_name_list, list):
        return jsonify({
            'success': False,
            'message': '缺少必需参数: file_name_list（必须是数组）'
        }), 400
    
    if len(file_name_list) == 0:
        return jsonify({
            'success': False,
            'message': 'file_name_list不能为空'
        }), 400
    
    request_id = data.get('request_id')
    
    # 发送上传文件命令
    success, req_id = mqtt_publisher.upload_file(camera_id, file_name_list, request_id)
    
    if success:
        return jsonify({
            'success': True,
            'camera_id': camera_id,
            'request_id': req_id,
            'file_name_list': file_name_list,
            'message': '文件上传命令已发送，请使用request_id查询结果和进度'
        })
    else:
        return jsonify({
            'success': False,
            'camera_id': camera_id,
            'message': '发送文件上传命令失败，请检查MQTT连接'
        }), 500


@main.route('/api/camera/<camera_id>/videos/upload/status', methods=['GET', 'POST'])
def get_upload_progress(camera_id):
    """
    查询摄像头的文件上传进度
    
    Args:
        camera_id: 摄像头ID
        
    Query Params (GET) 或 Request Body (POST):
        {
            "file_name_list": ["vid_001", "vid_002"],  # 可选，要查询的文件列表
            "request_id": "optional",                   # 可选的请求ID
            "query_device": false                       # 是否主动查询设备（默认false，直接返回缓存）
        }
    
    Returns:
        JSON格式的上传进度
    """
    data = {}
    if request.method == 'POST' and request.is_json:
        data = request.get_json()
    elif request.method == 'GET':
        data = request.args.to_dict()
    
    query_device = data.get('query_device', 'false').lower() == 'true'
    
    if query_device:
        # 主动查询设备的上传进度
        file_name_list = data.get('file_name_list')
        if file_name_list and isinstance(file_name_list, str):
            # 如果是字符串，尝试解析为列表
            try:
                import json
                file_name_list = json.loads(file_name_list)
            except:
                file_name_list = None
        
        request_id = data.get('request_id')
        success, req_id = mqtt_publisher.get_upload_status(camera_id, file_name_list, request_id)
        
        if not success:
            return jsonify({
                'success': False,
                'camera_id': camera_id,
                'message': '发送上传进度查询命令失败，请检查MQTT连接'
            }), 500
        
        return jsonify({
            'success': True,
            'camera_id': camera_id,
            'request_id': req_id,
            'message': '上传进度查询命令已发送，请稍后再次查询或等待设备上报'
        })
    else:
        # 直接返回缓存的上传进度
        progress = upload_progress_manager.get_camera_progress(camera_id)
        
        return jsonify({
            'success': True,
            'camera_id': camera_id,
            'progress': progress,
            'count': len(progress)
        })


# ==================== 任务历史接口 ====================

@main.route('/api/camera/<camera_id>/tasks', methods=['GET'])
def get_camera_tasks(camera_id):
    """
    获取指定摄像头的操作历史（从task表）
    
    查询参数:
    - limit: 返回记录数量限制（默认50）
    
    返回格式:
    {
        "success": true,
        "camera_id": "HW-2024-001",
        "count": 10,
        "tasks": [
            {
                "id": 1,
                "requestid": "req_1234567890",
                "requesttype": "start_record",
                "state": "success",
                "description": "启动录制命令已下发 (场景: 702房间)",
                "created_at": "2025-11-08 10:00:00",
                "updated_at": "2025-11-08 10:00:05"
            }
        ]
    }
    """
    try:
        limit = request.args.get('limit', 50, type=int)
        
        # 获取client_id（因为task表使用client_id存储）
        client_id = get_client_id_by_hardware_id(camera_id)
        if not client_id:
            return jsonify({
                'success': False,
                'message': f'未找到设备: {camera_id}',
                'tasks': []
            }), 404
        
        # 从数据库查询该设备的任务列表
        tasks = list_tasks(clientid=client_id, limit=limit)
        
        return jsonify({
            'success': True,
            'camera_id': camera_id,
            'client_id': client_id,
            'count': len(tasks),
            'tasks': tasks
        })
    except Exception as e:
        print(f"❌ 获取任务历史失败: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'message': f'获取任务历史失败: {str(e)}',
            'tasks': []
        }), 500


@main.route('/api/tasks', methods=['GET'])
def get_all_tasks():
    """
    获取所有设备的操作历史
    
    查询参数:
    - limit: 返回记录数量限制（默认200）
    
    返回格式:
    {
        "success": true,
        "count": 50,
        "tasks": [...]
    }
    """
    try:
        limit = request.args.get('limit', 200, type=int)
        
        # 查询所有任务
        tasks = list_tasks(limit=limit)
        
        return jsonify({
            'success': True,
            'count': len(tasks),
            'tasks': tasks
        })
    except Exception as e:
        print(f"❌ 获取任务历史失败: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'message': f'获取任务历史失败: {str(e)}',
            'tasks': []
        }), 500
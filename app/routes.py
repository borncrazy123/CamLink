from flask import Blueprint, render_template
import requests
from requests.auth import HTTPBasicAuth

main = Blueprint('main', __name__)

@main.route('/')
def home():
    return render_template('device_manage.html')
    # return render_template('index.html')

@main.route('/camera_config')
def camera_config():
    return render_template('camera_config.html')

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
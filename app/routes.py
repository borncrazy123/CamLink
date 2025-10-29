from flask import Blueprint, render_template
import requests
from requests.auth import HTTPBasicAuth

main = Blueprint('main', __name__)

@main.route('/')
def home():
    return render_template('index.html')

@main.route('/hello')
def hello():
    return "Hello, World!"

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
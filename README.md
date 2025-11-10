# CamLink

CamLink 是一个基于 Flask 框架开发的 Web 应用程序。

## 项目结构

```
CamLink/
├── README.md
├── requirements.txt
├── run.py
└── app/
    ├── __init__.py
    ├── routes.py
    ├── static/
    │   └── style.css
    └── templates/
        └── index.html
```

## 技术栈

- Python 3.x
- Flask 3.0.3
- HTML/CSS

## 快速开始

### 1. 环境准备

确保你的系统已安装 Python 3.x 版本。

### 2. 安装依赖

```bash
pip install -r requirements.txt
```

### 3. 运行应用

```bash
python run.py
```

### 4. 服务器上运行应用
```bash
nohup python3 run.py > /root/canvas/log/run.log 2>&1 &
```

启动后，访问 http://localhost:5000 即可查看应用。

## 开发

- `run.py` - 应用程序入口点
- `app/routes.py` - 路由定义
- `app/templates/` - HTML 模板文件
- `app/static/` - 静态资源文件（CSS、JavaScript、图片等）

## 许可证

[MIT License](https://opensource.org/licenses/MIT)
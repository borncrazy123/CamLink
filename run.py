from app import create_app
import threading
from app.src.monitor_cam import create_status_listener
from app.src.sqllite import init_db, init_task_table
import os

app = create_app()

if __name__ == "__main__":
    # --- 初始化数据库 ---
    print("🗄️  初始化数据库...")
    try:
        init_db()  # 初始化设备表
        init_task_table()  # 初始化任务表
        print("✅ 数据库初始化完成")
    except Exception as e:
        print(f"❌ 数据库初始化失败: {e}")
    # --- 初始化数据库 ---
    
    # --- 后台线程启动状态监听器 ---
    if os.environ.get('WERKZEUG_RUN_MAIN') == 'true':
        status_listener_thread = threading.Thread(target=create_status_listener, daemon=True)
        status_listener_thread.start()
        print("✅ 摄像头状态监听器已在后台启动")
    # --- 后台线程启动状态监听器 ---

    app.run(debug=True, host='0.0.0.0', port=8080)

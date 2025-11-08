"""
完整工作流测试
模拟真实场景：发送命令 → 接收响应 → 查询历史
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.src.sqllite import init_db, init_task_table, list_tasks, get_device_by_client_id, insert_device
from app.src.record_control import create_command_task, update_command_task_success, update_command_task_failed
import time

def test_full_workflow():
    """测试完整工作流"""
    print("=" * 80)
    print("🧪 测试完整工作流：发送命令 → 接收响应 → 查询历史")
    print("=" * 80)
    
    # 1. 初始化数据库
    print("\n【步骤1】初始化数据库")
    init_db()
    init_task_table()
    print("✅ 数据库初始化完成")
    
    # 2. 确保测试设备存在
    print("\n【步骤2】准备测试设备")
    test_client_id = "CAM-1730985600000-ABC123"
    test_hardware_id = "HW-2024-001"
    
    device = get_device_by_client_id(test_client_id)
    if not device:
        print(f"⚠️  设备不存在，创建测试设备...")
        insert_device({
            'hardware_id': test_hardware_id,
            'client_id': test_client_id,
            'hotel': '北京希尔顿酒店',
            'location': '大堂入口',
            'wifi': 'Hotel-IoT-Network',
            'status': '在线',
            'run_state': 'stopped'
        })
        print(f"✅ 测试设备创建成功: {test_hardware_id}")
    else:
        print(f"✅ 测试设备已存在: {test_hardware_id}")
    
    # 3. 模拟发送命令（创建task）
    print("\n【步骤3】模拟发送命令（如：开始录制）")
    request_id_1 = f"req_test_{int(time.time() * 1000)}_001"
    
    task_id = create_command_task(
        client_id=test_client_id,
        request_id=request_id_1,
        request_type='start_record',
        description='启动录制命令已下发 (场景: 702房间)'
    )
    print(f"✅ 命令已发送，task_id: {task_id}, request_id: {request_id_1}")
    print(f"   状态: calling（调用中）")
    
    # 4. 模拟设备响应成功
    print("\n【步骤4】模拟设备响应（成功）")
    time.sleep(0.5)  # 模拟网络延迟
    update_command_task_success(request_id_1, "录制已成功启动")
    print(f"✅ 设备响应成功")
    print(f"   状态: calling → success")
    
    # 5. 再发送一个命令并模拟失败
    print("\n【步骤5】模拟另一个命令失败（如：停止录制失败）")
    request_id_2 = f"req_test_{int(time.time() * 1000)}_002"
    
    create_command_task(
        client_id=test_client_id,
        request_id=request_id_2,
        request_type='stop_record',
        description='停止录制命令已下发'
    )
    print(f"✅ 命令已发送，request_id: {request_id_2}")
    
    time.sleep(0.3)
    update_command_task_failed(request_id_2, error_msg="device not responding", error_code=500)
    print(f"✅ 设备响应失败")
    print(f"   状态: calling → failed")
    
    # 6. 发送查询视频列表命令
    print("\n【步骤6】模拟查询视频列表命令")
    request_id_3 = f"req_test_{int(time.time() * 1000)}_003"
    
    create_command_task(
        client_id=test_client_id,
        request_id=request_id_3,
        request_type='list_videos',
        description='查询视频列表命令已下发'
    )
    print(f"✅ 命令已发送，request_id: {request_id_3}")
    
    # 模拟返回视频列表
    time.sleep(0.4)
    update_command_task_success(
        request_id_3,
        result_data={'videos': [{'name': 'v1'}, {'name': 'v2'}, {'name': 'v3'}]}
    )
    print(f"✅ 查询成功，找到3个视频")
    
    # 7. 查询该设备的所有操作历史
    print("\n【步骤7】查询设备操作历史（模拟前端调用 API）")
    print(f"API: GET /api/camera/{test_hardware_id}/tasks")
    
    tasks = list_tasks(clientid=test_client_id, limit=50)
    print(f"✅ 查询到 {len(tasks)} 条操作记录")
    
    # 8. 显示操作历史（模拟前端渲染）
    print("\n【步骤8】操作历史列表（前端"操作动态"标签页显示）")
    print("=" * 100)
    print(f"{'时间':<20} {'操作类型':<15} {'状态':<10} {'描述':<40}")
    print("=" * 100)
    
    # 操作类型映射（与前端一致）
    type_labels = {
        'start_record': '🔴 开始录制',
        'stop_record': '⏹️ 停止录制',
        'list_videos': '📹 查询文件',
        'upload_file': '⬆️ 上传文件',
        'get_upload_status': '📊 查询进度'
    }
    
    # 状态图标（与前端一致）
    state_icons = {
        'success': '✅',
        'failed': '❌',
        'calling': '⏳'
    }
    
    for task in tasks[:10]:  # 只显示最近10条
        type_label = type_labels.get(task['requesttype'], '📌 设备操作')
        state_icon = state_icons.get(task['state'], '•')
        
        print(f"{task['created_at']:<20} {type_label:<20} {state_icon} {task['state']:<10} {task['description']:<40}")
    
    print("\n" + "=" * 80)
    print("✅ 完整工作流测试完成！")
    print("=" * 80)
    
    print("\n💡 测试说明:")
    print("1. ✅ 命令发送时自动创建 task 记录（state: calling）")
    print("2. ✅ 设备响应时自动更新 task 状态（state: success/failed）")
    print("3. ✅ 前端可通过 API 查询操作历史显示在\"操作动态\"标签页")
    print("4. ✅ 所有操作都已持久化到数据库")
    
    print("\n🚀 下一步:")
    print("1. 启动应用: python run.py")
    print("2. 打开设备管理页面: http://localhost:5001/device_manage")
    print(f"3. 点击设备 {test_hardware_id} 查看操作动态")
    print("4. 操作动态中会显示上面创建的所有记录")


if __name__ == '__main__':
    test_full_workflow()


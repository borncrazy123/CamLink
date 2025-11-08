"""
测试任务追踪系统
验证task表的创建和更新功能
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.src.sqllite import init_db, init_task_table, list_tasks, get_device_by_client_id
from app.src.record_control import (
    create_command_task,
    update_command_task_success,
    update_command_task_failed
)

def test_task_tracking():
    """测试任务追踪功能"""
    print("=" * 60)
    print("🧪 测试任务追踪系统")
    print("=" * 60)
    
    # 1. 初始化数据库
    print("\n1️⃣ 初始化数据库...")
    init_db()
    init_task_table()
    print("✅ 数据库初始化完成")
    
    # 2. 创建测试任务
    print("\n2️⃣ 创建测试任务...")
    test_client_id = "CAM-1730985600000-ABC123"
    test_request_id = "req_test_12345"
    
    task_id = create_command_task(
        client_id=test_client_id,
        request_id=test_request_id,
        request_type='start_record',
        description='测试：启动录制命令已下发 (场景: 测试房间)'
    )
    
    if task_id > 0:
        print(f"✅ 任务创建成功，task_id: {task_id}")
    else:
        print("❌ 任务创建失败")
        return
    
    # 3. 查询任务
    print("\n3️⃣ 查询刚创建的任务...")
    tasks = list_tasks(clientid=test_client_id, limit=10)
    print(f"✅ 查询到 {len(tasks)} 条任务记录")
    for task in tasks[:3]:  # 只显示前3条
        print(f"   - request_id: {task['requestid']}, type: {task['requesttype']}, state: {task['state']}")
    
    # 4. 模拟任务成功
    print("\n4️⃣ 模拟任务执行成功...")
    success = update_command_task_success(test_request_id, "测试：命令执行成功")
    if success:
        print("✅ 任务状态更新为成功")
    else:
        print("❌ 任务状态更新失败")
    
    # 5. 再次查询验证
    print("\n5️⃣ 验证任务状态更新...")
    tasks = list_tasks(clientid=test_client_id, limit=10)
    for task in tasks:
        if task['requestid'] == test_request_id:
            print(f"✅ 任务状态: {task['state']}, 描述: {task['description']}")
            break
    
    # 6. 创建第二个任务并测试失败场景
    print("\n6️⃣ 测试任务失败场景...")
    test_request_id_2 = "req_test_67890"
    task_id_2 = create_command_task(
        client_id=test_client_id,
        request_id=test_request_id_2,
        request_type='stop_record',
        description='测试：停止录制命令已下发'
    )
    
    # 模拟失败
    update_command_task_failed(
        test_request_id_2,
        error_msg="storage full",
        error_code=101
    )
    
    # 验证
    tasks = list_tasks(clientid=test_client_id, limit=10)
    for task in tasks:
        if task['requestid'] == test_request_id_2:
            print(f"✅ 任务状态: {task['state']}, 描述: {task['description']}")
            break
    
    # 7. 显示所有任务
    print("\n7️⃣ 显示该设备的所有任务...")
    all_tasks = list_tasks(clientid=test_client_id, limit=50)
    print(f"✅ 共有 {len(all_tasks)} 条任务记录")
    print("\n任务列表:")
    print("-" * 100)
    print(f"{'ID':<5} {'请求ID':<20} {'类型':<15} {'状态':<10} {'描述':<30} {'创建时间':<20}")
    print("-" * 100)
    for task in all_tasks[:10]:  # 只显示前10条
        print(f"{task['id']:<5} {task['requestid']:<20} {task['requesttype']:<15} "
              f"{task['state']:<10} {task['description']:<30} {task['created_at']:<20}")
    
    print("\n" + "=" * 60)
    print("✅ 任务追踪系统测试完成！")
    print("=" * 60)


if __name__ == '__main__':
    test_task_tracking()


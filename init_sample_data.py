"""
向数据库中插入示例设备数据
运行此脚本可以快速填充测试数据
"""
from app.src.sqllite import init_db, insert_device, list_devices

# 示例设备数据
SAMPLE_DEVICES = [
    {
        'hardware_id': 'HW-2024-001',
        'client_id': 'CAM-1730985600000-ABC123',
        'hotel': '北京希尔顿酒店',
        'location': '大堂入口',
        'wifi': 'Hotel-IoT-Network',
        'runtime': '15天 8小时',
        'fw': 'v2.1.3',
        'last_online': '2025-11-08 16:28:45',
        'status': '在线',
        'run_state': 'stopped',
        'left_storage': 35,
        'electric_percent': 65,
        'network_signal_strength': -55
    },
    {
        'hardware_id': 'HW-2024-002',
        'client_id': 'CAM-1730985600001-DEF456',
        'hotel': '北京希尔顿酒店',
        'location': '电梯厅 - 2F',
        'wifi': 'Hotel-IoT-Network',
        'runtime': '15天 8小时',
        'fw': 'v2.1.3',
        'last_online': '2025-11-08 16:28:45',
        'status': '在线',
        'run_state': 'recording',
        'left_storage': 28,
        'electric_percent': 70,
        'network_signal_strength': -52
    },
    {
        'hardware_id': 'HW-2024-003',
        'client_id': 'CAM-1730985600002-GHI789',
        'hotel': '上海香格里拉酒店',
        'location': '停车场入口',
        'wifi': 'Hotel-Shanghai-IoT',
        'runtime': '0天 0小时',
        'fw': 'v2.0.9',
        'last_online': '2025-11-08 15:28:45',
        'status': '离线',
        'run_state': 'stopped',
        'left_storage': 0,
        'electric_percent': 0,
        'network_signal_strength': 0
    },
    {
        'hardware_id': 'HW-2024-004',
        'client_id': 'CAM-1730985600003-JKL012',
        'hotel': '广州万豪酒店',
        'location': '餐厅区域',
        'wifi': 'Hotel-GZ-IoT',
        'runtime': '2天 3小时',
        'fw': 'v2.1.2',
        'last_online': '2025-11-08 14:28:45',
        'status': '离线',
        'run_state': 'stopped',
        'left_storage': 5,
        'electric_percent': 20,
        'network_signal_strength': -75
    },
    {
        'hardware_id': 'HW-2024-005',
        'client_id': 'CAM-1730985600004-MNO345',
        'hotel': '深圳洲际酒店',
        'location': '会议室走廊',
        'wifi': 'Hotel-SZ-IoT',
        'runtime': '30天 12小时',
        'fw': 'v2.1.3',
        'last_online': '2025-11-08 16:28:45',
        'status': '在线',
        'run_state': 'stopped',
        'left_storage': 42,
        'electric_percent': 85,
        'network_signal_strength': -48
    }
]

def main():
    print("=" * 50)
    print("初始化数据库并插入示例数据")
    print("=" * 50)
    
    # 初始化数据库
    print("\n1. 初始化数据库表...")
    init_db()
    print("✅ 数据库表创建成功")
    
    # 插入示例数据
    print("\n2. 插入示例设备数据...")
    for device in SAMPLE_DEVICES:
        try:
            # 尝试插入，如果已存在则忽略
            device_id = insert_device(device)
            print(f"✅ 插入设备: {device['hardware_id']} (ID: {device_id})")
        except Exception as e:
            # 如果设备已存在，可能会报错，这里忽略
            if "UNIQUE constraint failed" in str(e):
                print(f"⚠️  设备已存在: {device['hardware_id']}")
            else:
                print(f"❌ 插入失败: {device['hardware_id']} - {e}")
    
    # 显示当前所有设备
    print("\n3. 当前数据库中的所有设备:")
    print("-" * 50)
    devices = list_devices()
    for device in devices:
        print(f"📷 {device['hardware_id']:<15} | {device['hotel']:<20} | {device['location']:<15} | {device['status']}")
    
    print("\n" + "=" * 50)
    print(f"✅ 完成！共有 {len(devices)} 台设备")
    print("=" * 50)

if __name__ == '__main__':
    main()


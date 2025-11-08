# 📋 任务追踪系统使用指南

## 🎯 系统概述

任务追踪系统通过 `tasks` 表记录所有摄像头操作（启动录制、停止录制、获取文件列表、上传文件等），实现操作历史的持久化存储，供前端页面查询展示。

---

## 📊 数据库表结构

```sql
CREATE TABLE IF NOT EXISTS tasks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    clientid TEXT NOT NULL,              -- 摄像头client_id（MQTT通信标识）
    requestid TEXT UNIQUE NOT NULL,      -- 请求ID（唯一标识）
    requesttype TEXT,                    -- 操作类型
    state TEXT,                          -- 任务状态
    description TEXT,                    -- 操作描述
    created_at TEXT DEFAULT (datetime('now')),  -- 创建时间
    updated_at TEXT                      -- 更新时间
);
```

### 字段说明

| 字段 | 类型 | 说明 | 示例值 |
|------|------|------|--------|
| `id` | INTEGER | 自增主键 | 1 |
| `clientid` | TEXT | MQTT通信用的client_id | `CAM-1730985600000-ABC123` |
| `requestid` | TEXT | 请求的唯一标识 | `req_1730985600000_1234` |
| `requesttype` | TEXT | 操作类型 | `start_record`, `stop_record`, `list_videos`, `upload_file`, `get_upload_status` |
| `state` | TEXT | 任务状态 | `calling`（调用中）, `success`（成功）, `failed`（失败） |
| `description` | TEXT | 操作描述（中文） | `启动录制命令已下发 (场景: 702房间)` |
| `created_at` | TEXT | 创建时间（自动） | `2025-11-08 10:00:00` |
| `updated_at` | TEXT | 更新时间 | `2025-11-08 10:00:05` |

---

## 🔄 工作流程

### 1. 命令发送阶段（创建任务）

当通过 `mqtt_publisher` 发送命令时，自动创建任务记录：

```python
# 示例：启动录制
success, request_id = mqtt_publisher.start_record(
    camera_id="HW-2024-001",
    pre_name="702房间"
)

# 内部会自动调用：
create_command_task(
    client_id="CAM-1730985600000-ABC123",
    request_id=request_id,
    request_type='start_record',
    description='启动录制命令已下发 (场景: 702房间)'
)
```

**初始状态**: `state = 'calling'`

### 2. 响应接收阶段（更新任务）

当通过 `status_listener` 接收到设备响应时，自动更新任务状态：

**成功响应**:
```json
{
  "request_id": "req_1730985600000_1234",
  "result": "success"
}
```
→ 更新为 `state = 'success'`

**失败响应**:
```json
{
  "request_id": "req_1730985600000_1234",
  "result": "failed",
  "error_code": 101,
  "error_msg": "storage full"
}
```
→ 更新为 `state = 'failed'`, `description = '执行失败 (错误码: 101): storage full'`

---

## 🎨 前端集成

### API接口

#### 1. 获取单个设备的操作历史

**请求**:
```http
GET /api/camera/{camera_id}/tasks?limit=50
```

**响应**:
```json
{
  "success": true,
  "camera_id": "HW-2024-001",
  "client_id": "CAM-1730985600000-ABC123",
  "count": 10,
  "tasks": [
    {
      "id": 1,
      "requestid": "req_1730985600000_1234",
      "requesttype": "start_record",
      "state": "success",
      "description": "启动录制命令已下发 (场景: 702房间)",
      "created_at": "2025-11-08 10:00:00",
      "updated_at": "2025-11-08 10:00:05"
    },
    {
      "id": 2,
      "requestid": "req_1730985600000_5678",
      "requesttype": "stop_record",
      "state": "success",
      "description": "停止录制命令已下发",
      "created_at": "2025-11-08 10:05:00",
      "updated_at": "2025-11-08 10:05:03"
    }
  ]
}
```

#### 2. 获取所有设备的操作历史

**请求**:
```http
GET /api/tasks?limit=200
```

**响应**:
```json
{
  "success": true,
  "count": 50,
  "tasks": [...]
}
```

### 前端实现示例（JavaScript）

```javascript
// 获取设备操作历史
async function loadDeviceTimeline(cameraId) {
    try {
        const response = await fetch(`/api/camera/${cameraId}/tasks?limit=50`);
        const data = await response.json();
        
        if (data.success) {
            displayTimeline(data.tasks);
        } else {
            showToast('加载操作历史失败', 'error');
        }
    } catch (error) {
        console.error('加载操作历史失败:', error);
        showToast('加载操作历史失败', 'error');
    }
}

// 显示时间线
function displayTimeline(tasks) {
    const timelineHtml = tasks.map(task => {
        const stateClass = {
            'calling': 'timeline-calling',
            'success': 'timeline-success',
            'failed': 'timeline-failed'
        }[task.state] || '';
        
        const stateIcon = {
            'calling': '⏳',
            'success': '✅',
            'failed': '❌'
        }[task.state] || '•';
        
        return `
            <div class="timeline-item ${stateClass}">
                <div class="timeline-icon">${stateIcon}</div>
                <div class="timeline-content">
                    <div class="timeline-title">${task.description}</div>
                    <div class="timeline-meta">
                        <span>${task.created_at}</span>
                        <span class="timeline-type">${getTypeLabel(task.requesttype)}</span>
                    </div>
                </div>
            </div>
        `;
    }).join('');
    
    document.getElementById('timelineContent').innerHTML = timelineHtml;
}

// 操作类型标签映射
function getTypeLabel(type) {
    const labels = {
        'start_record': '开始录制',
        'stop_record': '停止录制',
        'list_videos': '查询文件',
        'upload_file': '上传文件',
        'get_upload_status': '查询进度'
    };
    return labels[type] || type;
}
```

---

## 🧪 测试验证

运行测试脚本验证任务追踪系统：

```bash
python test_task_tracking.py
```

测试内容：
1. ✅ 数据库初始化
2. ✅ 创建任务记录
3. ✅ 查询任务列表
4. ✅ 更新任务为成功
5. ✅ 更新任务为失败
6. ✅ 显示任务历史

---

## 📈 支持的操作类型

| 操作类型 | requesttype | 说明 |
|---------|-------------|------|
| 开始录制 | `start_record` | 启动摄像头录制 |
| 停止录制 | `stop_record` | 停止摄像头录制 |
| 查询视频列表 | `list_videos` | 获取视频文件列表 |
| 上传文件 | `upload_file` | 请求上传指定文件 |
| 查询上传进度 | `get_upload_status` | 获取文件上传进度 |
| 获取设备状态 | `get_status` | 查询设备实时状态 |

---

## 🎯 状态转换图

```
[创建任务]
    ↓
state: calling (调用中)
    ↓
[设备响应]
    ↓
   ┌─────────────┐
   │             │
   ↓             ↓
success       failed
(成功)        (失败)
```

---

## 💡 最佳实践

### 1. 命令发送
- ✅ 每次发送MQTT命令都会自动创建task记录
- ✅ request_id会自动生成（`req_{timestamp}_{random}`）
- ✅ 无需手动调用task创建函数

### 2. 响应处理
- ✅ MQTT监听器会自动更新task状态
- ✅ 成功/失败状态自动识别
- ✅ 错误信息自动记录到description

### 3. 前端查询
- ✅ 使用hardware_id查询（API会自动转换为client_id）
- ✅ 支持分页（limit参数）
- ✅ 按创建时间倒序排列（最新的在前）

---

## 🔧 扩展开发

### 添加新的操作类型

1. 在 `mqtt_publisher.py` 中添加新的发送方法
2. 在方法中调用 `create_command_task` 创建任务
3. 在 `status_listener.py` 中处理对应的响应
4. 响应处理中调用 `update_command_task_success/failed`

示例：
```python
# mqtt_publisher.py
def my_new_command(self, camera_id: str, request_id: str = None):
    # ... 发送MQTT命令 ...
    create_command_task(
        client_id=client_id,
        request_id=request_id,
        request_type='my_new_command',
        description='新命令已下发'
    )
```

---

## 📞 联系与反馈

如有问题或建议，请联系开发团队。


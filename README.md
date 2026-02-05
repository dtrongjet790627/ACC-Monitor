# ACC Monitor System

ACC监控平台 - 航驱汽车生产线监控系统

## 项目结构

```
ACC-Monitor/
├── backend/                 # Flask后端
│   ├── app/
│   │   ├── api/            # REST API和WebSocket
│   │   ├── models/         # 数据库模型
│   │   ├── services/       # 业务逻辑服务
│   │   └── utils/          # 工具类和调度器
│   ├── config/             # 配置文件
│   ├── data/               # SQLite数据库
│   └── run.py              # 应用入口
├── frontend/               # Vue.js前端 (待开发)
├── agents/                 # 采集Agent
│   ├── windows/            # Windows Agent
│   └── linux/              # Linux Agent
└── ui-design/              # UI设计稿
```

## 功能模块

### 已实现

1. **服务器监控**
   - 监控7台服务器状态
   - 进程状态检测
   - CPU/内存/磁盘监控
   - WebSocket实时推送

2. **自动重启**
   - 检测进程停止自动重启
   - 重启前收集日志
   - 重启历史记录

3. **数据库监控**
   - Oracle表空间使用率
   - 告警阈值：>85%警告，>95%严重
   - 一键优化功能

4. **日志监控**
   - 实时扫描日志关键词
   - 多级别告警
   - 日志搜索

5. **告警系统**
   - 告警分级
   - 告警确认
   - 实时推送

### 待开发

- EAI容器磁盘监控
- 工站报警分类
- 企业微信通知
- 历史趋势图表

## 快速开始

### 后端启动

```bash
cd backend

# 安装依赖
pip install -r requirements.txt

# 配置环境变量
cp .env.example .env
# 编辑.env文件配置数据库密码等

# 启动服务
python run.py
```

访问：http://localhost:5000/api/health

### Agent部署

#### Windows服务器

```powershell
cd agents/windows

# 安装依赖
pip install -r requirements.txt

# 配置config.json中的server_url和server_id

# 安装为Windows服务
.\install_service.ps1
```

#### Linux服务器 (EAI)

```bash
cd agents/linux

# 安装
chmod +x install.sh
sudo ./install.sh
```

## API文档

### Dashboard

| 接口 | 方法 | 说明 |
|------|------|------|
| /api/dashboard/overview | GET | 获取总览数据 |

### 服务器

| 接口 | 方法 | 说明 |
|------|------|------|
| /api/servers | GET | 获取服务器列表 |
| /api/servers/{id} | GET | 获取服务器详情 |
| /api/servers/{id}/status | GET | 获取服务器状态 |
| /api/servers/{id}/processes | GET | 获取进程列表 |

### 数据库

| 接口 | 方法 | 说明 |
|------|------|------|
| /api/databases | GET | 获取数据库列表 |
| /api/databases/{id}/tablespaces | GET | 获取表空间状态 |
| /api/databases/{id}/optimize | POST | 一键优化 |

### 告警

| 接口 | 方法 | 说明 |
|------|------|------|
| /api/alerts | GET | 获取告警列表 |
| /api/alerts/{id}/ack | POST | 确认告警 |

### 日志

| 接口 | 方法 | 说明 |
|------|------|------|
| /api/logs/search | POST | 搜索日志 |
| /api/logs/statistics | GET | 日志统计 |

### WebSocket

| 事件 | 说明 |
|------|------|
| connect | 连接成功 |
| request_status | 请求状态更新 |
| server_status_update | 服务器状态推送 |
| new_alert | 新告警推送 |

## 监控服务器

| 编号 | 名称 | IP | 监控内容 |
|------|------|-----|----------|
| 164 | 电控一线 | 172.17.10.164 | ACC进程、Oracle |
| 168 | 电控二线 | 172.17.10.168 | ACC进程、Oracle |
| 153 | DP EPS | 172.17.10.153 | ACC进程、Oracle |
| 193 | C EPS | 172.17.10.193 | ACC进程、Oracle |
| 194 | L EPP | 172.17.10.194 | ACC进程、Oracle |
| 165 | 共用服务器 | 172.17.10.165 | Oracle、Web服务 |
| 163 | EAI服务器 | 172.17.10.163 | Docker容器 |

## 技术栈

- **后端**：Flask, Flask-SocketIO, SQLAlchemy
- **数据库**：SQLite (本地), Oracle (监控目标)
- **前端**：Vue.js, ECharts (待开发)
- **Agent**：Python, psutil, paramiko

## 负责人

- 技术开发：程远
- UI设计：林曦
- 运维部署：韩大师
- 项目协调：陈默

---
*版本: V1.0 | 日期: 2026-01-29*

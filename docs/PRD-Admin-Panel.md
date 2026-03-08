# PRD: ACC Monitor Admin Panel (Backend Management Interface)

> Version: V1.0
> Author: Su Jin (Product Director)
> Date: 2026-02-10
> Status: Draft
> Priority: P1 - High

---

## 1. Background & Objectives

### 1.1 Background

ACC Monitor currently manages 8 servers via a hardcoded Python dictionary (`SERVERS`) in `backend/config/settings.py`. Every time we need to add a new server, modify service items, or toggle display settings, we must manually edit the source code and restart the backend service. This workflow has the following problems:

- Maintenance cost is high: requires developer intervention for simple configuration changes
- Risk of errors: manual editing of Python dict can introduce syntax errors
- No audit trail: changes are not tracked or versioned
- Downtime required: backend must restart for configuration changes to take effect

### 1.2 Objectives

Build a backend management interface ("Admin Panel") that allows authorized users to:

1. Manage server cards (CRUD operations) without touching source code
2. Manage service/process monitoring items per server
3. Control visibility of servers and service items on the Dashboard
4. Configure Oracle database connections
5. Configure alert rule keywords
6. All changes take effect without restarting the backend service

### 1.3 User Stories

| ID | As a... | I want to... | So that... |
|----|---------|-------------|------------|
| US-01 | System admin | Add a new server to monitoring | New production servers are automatically monitored |
| US-02 | System admin | Edit server configuration (IP, name, credentials) | I can update server info when network changes |
| US-03 | System admin | Toggle server visibility on Dashboard | I can hide decommissioned servers without deleting data |
| US-04 | System admin | Add/remove service items for a server | I can adjust which services are monitored per server |
| US-05 | System admin | Toggle individual service visibility | I can hide irrelevant services from the Dashboard |
| US-06 | System admin | Reorder servers on the Dashboard | I can organize the layout logically |
| US-07 | System admin | Configure Oracle database connections | Database monitoring covers new instances |
| US-08 | System admin | Manage alert keywords | I can customize which log keywords trigger alerts |

---

## 2. Entry Point Design

### 2.1 Primary Entry: Settings Icon on Top Status Bar

**Location**: Top status bar (`<header class="top-status-bar">`), right side area, after the existing UPTIME and AVG PING indicators.

**Implementation**: Add a gear icon button at the far right of `status-right`.

```
[SYSTEM MONITOR]  TOTAL:8 ONLINE:8    [LIVE]    UPTIME:30 DAYS  AVG PING:12ms  [GEAR_ICON]
```

**Visual Design**:
- Icon: Unicode gear character or SVG icon, styled in the existing cyan/green cyberpunk palette
- Hover effect: Glow animation consistent with cyberpunk theme (neon cyan glow)
- Tooltip on hover: `"ADMIN PANEL // SYS-CONFIG"`
- Click action: Navigate to `/admin` route

### 2.2 Secondary Entry: Terminal Command

In the bottom System Log panel area, support typing a command:

```
> admin
```

or

```
> config
```

This provides a "hacker-style" entry consistent with the cyberpunk aesthetic.

### 2.3 Route Configuration

Add to `frontend/src/router/index.js`:

```javascript
{
  path: '/admin',
  name: 'Admin',
  component: () => import('@/views/Admin.vue'),
  meta: { title: 'Admin Panel' }
}
```

### 2.4 Return to Dashboard

The Admin Panel page should have a clear "BACK TO DASHBOARD" button in the top-left corner, and/or pressing `ESC` navigates back to `/`.

---

## 3. Feature Specifications

### 3.1 Server Management (CRUD)

#### 3.1.1 Server List View

A table/card list showing all servers with the following columns:

| Column | Source Field | Description |
|--------|-------------|-------------|
| Sort Order | `sort_order` | Drag handle or up/down arrows to reorder |
| Server ID | key (e.g., '153') | Short identifier, auto-generated or manual |
| Server Name | `name` | English name (e.g., 'DP EPS Production') |
| Display Name | `name_cn` | Short label shown on card (e.g., 'DP_EPS') |
| IP Address | `ip` | e.g., '172.17.10.153' |
| OS Type | `os` | Dropdown: `windows` / `linux` |
| Visible | (new field) `visible` | Toggle switch: show/hide on Dashboard |
| Status | (runtime) | Current online/offline status (read-only) |
| Actions | - | Edit / Delete / Manage Services |

#### 3.1.2 Add/Edit Server Form

Fields (mapped from current `SERVERS` dict structure):

| Field | Type | Required | Default | Notes |
|-------|------|----------|---------|-------|
| Server ID | Text input | Yes | Auto-gen | Unique identifier (e.g., '153') |
| Name | Text input | Yes | - | English name |
| Display Name (name_cn) | Text input | Yes | - | Short label for Dashboard card |
| IP Address | Text input | Yes | - | Validate IPv4 format |
| OS Type | Select | Yes | 'windows' | Options: windows, linux |
| ACC Drive Letter | Text input | Conditional | 'D' | Only for Windows servers. Which drive ACC is deployed to |
| Log Path | Text input | No | Auto-gen | Auto-generated from OS + acc_drive, editable |
| Has Oracle | Toggle | No | false | Whether this server runs Oracle DB |
| Oracle Type | Select | Conditional | 'line' | Only if has_oracle=true. Options: 'line' (production line DB), 'factory' (factory DB) |
| Sort Order | Number | No | Auto (last) | Position in Dashboard grid |
| Visible | Toggle | No | true | Show/hide on Dashboard |

**Validation Rules**:
- IP address must be valid IPv4 format
- Server ID must be unique
- Name and Display Name must not be empty
- If OS = 'linux', ACC Drive is not applicable

#### 3.1.3 Delete Server

- Confirmation dialog required: "Are you sure you want to delete server [name] ([ip])?"
- Soft delete recommended: mark as `deleted=true` rather than removing from database
- Deleting a server also hides all its services from monitoring

### 3.2 Service/Process Management

#### 3.2.1 Service List per Server

Accessed by clicking "Manage Services" on a server row. Shows all monitored services/processes for that server.

**For Windows Servers** (two categories):

**a) Processes (legacy process monitoring)**:

| Column | Source Field | Description |
|--------|-------------|-------------|
| Process Name | `processes[]` | e.g., 'Oracle' |
| Monitored | (new) `monitored` | Toggle: whether to actively check |
| Visible | (new) `visible` | Toggle: show/hide on Dashboard card |

**b) Services (NSSM/Windows services)**:

| Column | Source Field | Description |
|--------|-------------|-------------|
| Service Name | `services[].service_name` | Windows service name (e.g., 'ACC.Server') |
| Display Name | `services[].display_name` | Friendly name shown on Dashboard |
| Monitored | (new) `monitored` | Toggle: whether to actively check |
| Visible | (new) `visible` | Toggle: show/hide on Dashboard card |
| Auto Restart | (new) `auto_restart` | Toggle: whether to auto-restart if stopped |
| Actions | - | Edit / Delete |

**For Linux Servers** (containers):

| Column | Source Field | Description |
|--------|-------------|-------------|
| Container Name | `containers[]` | e.g., 'hulu-eai' |
| Monitored | (new) `monitored` | Toggle |
| Visible | (new) `visible` | Toggle |
| Container Metrics | `container_metrics` | Toggle: enable CPU/Memory/Network monitoring |

**Monitored Metrics** (sub-table for Linux servers with `container_metrics=true`):

| Column | Source Field | Description |
|--------|-------------|-------------|
| Container | `monitored_metrics[].container` | Container name |
| Metric | `monitored_metrics[].metric` | cpu / memory / network |
| Display Name | `monitored_metrics[].display_name` | Label shown on Dashboard |
| Enabled | (new) `enabled` | Toggle |

#### 3.2.2 Add Service/Process

Form for adding a new service item:

| Field | Type | Required |
|-------|------|----------|
| Service Name | Text | Yes |
| Display Name | Text | Yes |
| Monitored | Toggle | Default: true |
| Visible | Toggle | Default: true |
| Auto Restart | Toggle | Default: false |

#### 3.2.3 Batch Operations

- "Toggle All Visible" button to show/hide all services at once
- "Toggle All Monitored" button to enable/disable all monitoring at once

### 3.3 Oracle Database Configuration

#### 3.3.1 Database Config List

Shows all Oracle database connections (mapped from `ORACLE_CONFIGS`):

| Column | Source Field | Description |
|--------|-------------|-------------|
| Server | Key + server name | Which server this DB belongs to |
| Host | `host` | Database host IP |
| Port | `port` | Default 1521 |
| Service Name | `service_name` | Oracle service name |
| Username | `username` | DB username |
| Tablespaces | `tablespaces` | Comma-separated list |
| Status | (runtime) | Connection test result |
| Actions | - | Edit / Test Connection / Delete |

#### 3.3.2 Add/Edit Database Config Form

| Field | Type | Required | Default |
|-------|------|----------|---------|
| Server | Select | Yes | - |
| Host | Text | Yes | Auto-fill from server IP |
| Port | Number | Yes | 1521 |
| Service Name | Text | Yes | 'ACC_DB' |
| Username | Text | Yes | 'ACC' |
| Password | Password | Yes | (encrypted storage) |
| Tablespaces | Tag input | No | ACC_DATA, USERS, SYSAUX, SYSTEM |

#### 3.3.3 Test Connection

"Test Connection" button that attempts to connect to the Oracle instance and returns success/failure with error details.

### 3.4 SSH Credentials Configuration

| Field | Type | Description |
|-------|------|-------------|
| Windows Username | Text | Default SSH username for Windows servers |
| Windows Key File | File path | SSH private key path |
| Linux Username | Text | Default SSH username for Linux servers |
| Linux Key File | File path | SSH private key path |
| Server-specific Port Overrides | Table | Per-server SSH port (e.g., server 163 uses port 2200) |

### 3.5 Alert Rules Configuration

#### 3.5.1 Alert Keywords Management

Mapped from `LOG_ALERT_KEYWORDS`:

| Level | Keywords | Actions |
|-------|----------|---------|
| Critical | ORA-00600, ORA-04031, System.OutOfMemoryException | Edit / Add / Remove |
| Error | Exception, Error, ORA-, Failed | Edit / Add / Remove |
| Warning | Warning, Connection refused, Timeout, Retry | Edit / Add / Remove |

#### 3.5.2 Add Keyword

- Select level (critical / error / warning)
- Input keyword text
- Test against sample log text (optional)

### 3.6 System Settings

| Setting | Type | Current Value | Description |
|---------|------|---------------|-------------|
| Process Check Interval | Number (seconds) | 30 | How often to check processes |
| Database Check Interval | Number (seconds) | 300 | How often to check databases |
| Log Scan Interval | Number (seconds) | 60 | How often to scan logs |
| Tablespace Warning Threshold | Number (%) | 85 | Warning level for tablespace usage |
| Tablespace Critical Threshold | Number (%) | 95 | Critical level for tablespace usage |
| Disk Warning Threshold | Number (%) | 80 | Warning level for disk usage |
| Disk Critical Threshold | Number (%) | 90 | Critical level for disk usage |
| Auto Restart Enabled | Toggle | true | Global auto-restart switch |
| Restart Cooldown | Number (seconds) | 300 | Min time between restarts |
| Agent Offline Timeout | Number (seconds) | 30 | Time before agent marked offline |

### 3.7 Process Restart Commands Configuration

Mapped from `PROCESS_RESTART_COMMANDS`:

| Process Name | Start Command | Stop Command | Actions |
|-------------|---------------|--------------|---------|
| ACC.Server | net start "ACC Server" | net stop "ACC Server" | Edit / Delete |
| ACC.MQ | net start "ACC MQ" | net stop "ACC MQ" | Edit / Delete |
| Pack.Server | net start "Pack Server" | net stop "Pack Server" | Edit / Delete |

Support adding new restart command mappings.

---

## 4. Data Storage & Migration Plan

### 4.1 Current State Analysis

Currently all configuration lives as Python dictionaries in `backend/config/settings.py`:

| Config | Variable | Structure |
|--------|----------|-----------|
| Servers | `SERVERS` | Dict of dicts, keyed by server ID (e.g., '153') |
| Oracle DBs | `ORACLE_CONFIGS` | Dict of dicts, keyed by server ID |
| SSH Creds | `SSH_CREDENTIALS` | Dict by OS type |
| SSH Ports | `SSH_PORTS` | Dict of server_id -> port |
| Alert Keywords | `LOG_ALERT_KEYWORDS` | Dict of level -> keyword list |
| Restart Commands | `PROCESS_RESTART_COMMANDS` | Dict of process -> commands |

### 4.2 Recommended Storage: SQLite (existing acc_monitor.db)

The project already uses SQLite via SQLAlchemy (`acc_monitor.db`). We should add new tables to this database for configuration management.

**Reasons**:
- Already in use, no new dependencies
- Supports transactions (safe concurrent reads/writes)
- Migration tools available (Flask-Migrate / Alembic)
- Single-file database, easy to backup

### 4.3 New Database Tables

#### 4.3.1 `admin_servers` (replaces SERVERS dict)

```sql
CREATE TABLE admin_servers (
    id              VARCHAR(10) PRIMARY KEY,     -- e.g., '153'
    name            VARCHAR(100) NOT NULL,        -- 'DP EPS Production'
    name_cn         VARCHAR(50),                  -- 'DP_EPS'
    ip              VARCHAR(15) NOT NULL,         -- '172.17.10.153'
    os_type         VARCHAR(20) DEFAULT 'windows',-- 'windows' or 'linux'
    acc_drive       VARCHAR(1),                   -- 'E' (Windows only)
    log_path        VARCHAR(255),                 -- 'E:\\iPlant.ACC\\Log'
    has_oracle      BOOLEAN DEFAULT FALSE,
    oracle_type     VARCHAR(20),                  -- 'line' or 'factory'
    sort_order      INTEGER DEFAULT 0,
    visible         BOOLEAN DEFAULT TRUE,
    deleted         BOOLEAN DEFAULT FALSE,
    created_at      DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at      DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

#### 4.3.2 `admin_services` (replaces services/processes arrays)

```sql
CREATE TABLE admin_services (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    server_id       VARCHAR(10) NOT NULL REFERENCES admin_servers(id),
    category        VARCHAR(20) NOT NULL,         -- 'process', 'service', 'container'
    service_name    VARCHAR(100) NOT NULL,         -- Windows service name or process name
    display_name    VARCHAR(100),                  -- Friendly display name
    monitored       BOOLEAN DEFAULT TRUE,
    visible         BOOLEAN DEFAULT TRUE,
    auto_restart    BOOLEAN DEFAULT FALSE,
    sort_order      INTEGER DEFAULT 0,
    created_at      DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at      DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

#### 4.3.3 `admin_container_metrics` (for Linux servers)

```sql
CREATE TABLE admin_container_metrics (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    server_id       VARCHAR(10) NOT NULL REFERENCES admin_servers(id),
    container_name  VARCHAR(100) NOT NULL,
    metric_type     VARCHAR(20) NOT NULL,          -- 'cpu', 'memory', 'network'
    display_name    VARCHAR(100),
    enabled         BOOLEAN DEFAULT TRUE,
    created_at      DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

#### 4.3.4 `admin_oracle_configs` (replaces ORACLE_CONFIGS dict)

```sql
CREATE TABLE admin_oracle_configs (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    server_id       VARCHAR(10) NOT NULL REFERENCES admin_servers(id),
    host            VARCHAR(15) NOT NULL,
    port            INTEGER DEFAULT 1521,
    service_name    VARCHAR(50) NOT NULL,
    username        VARCHAR(50) NOT NULL,
    password_hash   VARCHAR(255),                  -- Encrypted password
    tablespaces     TEXT,                           -- JSON array: ["ACC_DATA", "USERS", ...]
    created_at      DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at      DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

#### 4.3.5 `admin_ssh_configs` (replaces SSH_CREDENTIALS + SSH_PORTS)

```sql
CREATE TABLE admin_ssh_configs (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    scope           VARCHAR(20) NOT NULL,          -- 'global_windows', 'global_linux', or server_id
    username        VARCHAR(50),
    key_file        VARCHAR(255),
    port            INTEGER DEFAULT 22,
    created_at      DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at      DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

#### 4.3.6 `admin_alert_keywords` (replaces LOG_ALERT_KEYWORDS dict)

```sql
CREATE TABLE admin_alert_keywords (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    level           VARCHAR(20) NOT NULL,          -- 'critical', 'error', 'warning'
    keyword         VARCHAR(200) NOT NULL,
    enabled         BOOLEAN DEFAULT TRUE,
    created_at      DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

#### 4.3.7 `admin_restart_commands` (replaces PROCESS_RESTART_COMMANDS dict)

```sql
CREATE TABLE admin_restart_commands (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    process_name    VARCHAR(100) NOT NULL,
    start_command   VARCHAR(500),
    stop_command    VARCHAR(500),
    os_type         VARCHAR(20) DEFAULT 'windows',
    created_at      DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at      DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

#### 4.3.8 `admin_system_settings` (replaces Config class constants)

```sql
CREATE TABLE admin_system_settings (
    key             VARCHAR(50) PRIMARY KEY,
    value           TEXT NOT NULL,
    value_type      VARCHAR(20) DEFAULT 'string',  -- 'string', 'number', 'boolean'
    description     VARCHAR(200),
    updated_at      DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

### 4.4 Migration Strategy

**Phase 1: Backward Compatible (V1)**
1. Create all `admin_*` tables
2. Write a one-time migration script that reads current `settings.py` values and inserts them into the new tables
3. Modify backend services to read from DB with fallback to `settings.py`
4. Logic: `load_config()` checks DB first; if empty, falls back to `settings.py` constants

**Phase 2: DB Primary (V2)**
1. Remove fallback to `settings.py` hardcoded values
2. `settings.py` only retains base Config class (SECRET_KEY, DB URI, etc.)
3. All server/service configs come exclusively from the database

**Migration Script Pseudocode**:
```python
def migrate_settings_to_db():
    """One-time migration from settings.py to database"""
    from config.settings import SERVERS, ORACLE_CONFIGS, SSH_CREDENTIALS, SSH_PORTS
    from config.settings import LOG_ALERT_KEYWORDS, PROCESS_RESTART_COMMANDS

    # 1. Migrate servers
    for server_id, config in SERVERS.items():
        admin_server = AdminServer(
            id=server_id,
            name=config['name'],
            name_cn=config.get('name_cn', ''),
            ip=config['ip'],
            os_type=config.get('os', 'windows'),
            acc_drive=config.get('acc_drive'),
            log_path=config.get('log_path'),
            has_oracle=config.get('has_oracle', False),
            oracle_type=config.get('oracle_type'),
            sort_order=config.get('sort_order', 0),
            visible=True
        )
        db.session.add(admin_server)

        # Migrate processes
        for proc in config.get('processes', []):
            service = AdminService(
                server_id=server_id,
                category='process',
                service_name=proc,
                display_name=proc,
                monitored=True,
                visible=True
            )
            db.session.add(service)

        # Migrate services
        for svc in config.get('services', []):
            service = AdminService(
                server_id=server_id,
                category='service',
                service_name=svc['service_name'],
                display_name=svc['display_name'],
                monitored=True,
                visible=True
            )
            db.session.add(service)

        # Migrate containers (Linux servers)
        for container in config.get('containers', []):
            service = AdminService(
                server_id=server_id,
                category='container',
                service_name=container,
                display_name=container,
                monitored=True,
                visible=True
            )
            db.session.add(service)

    # 2. Migrate Oracle configs
    for server_id, config in ORACLE_CONFIGS.items():
        oracle = AdminOracleConfig(
            server_id=server_id,
            host=config['host'],
            port=config['port'],
            service_name=config['service_name'],
            username=config['username'],
            tablespaces=json.dumps(config.get('tablespaces', []))
        )
        db.session.add(oracle)

    # 3. Migrate alert keywords
    for level, keywords in LOG_ALERT_KEYWORDS.items():
        for keyword in keywords:
            alert_kw = AdminAlertKeyword(
                level=level,
                keyword=keyword,
                enabled=True
            )
            db.session.add(alert_kw)

    db.session.commit()
```

---

## 5. API Design (Backend)

### 5.1 Admin Server APIs

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/admin/servers` | List all servers (including hidden) |
| GET | `/api/admin/servers/<id>` | Get single server config |
| POST | `/api/admin/servers` | Add new server |
| PUT | `/api/admin/servers/<id>` | Update server config |
| DELETE | `/api/admin/servers/<id>` | Soft-delete server |
| PUT | `/api/admin/servers/reorder` | Batch update sort_order |
| PUT | `/api/admin/servers/<id>/toggle-visible` | Toggle server visibility |

### 5.2 Admin Service APIs

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/admin/servers/<id>/services` | List services for a server |
| POST | `/api/admin/servers/<id>/services` | Add service to server |
| PUT | `/api/admin/services/<service_id>` | Update service config |
| DELETE | `/api/admin/services/<service_id>` | Delete service |
| PUT | `/api/admin/servers/<id>/services/batch` | Batch toggle monitored/visible |

### 5.3 Admin Oracle Config APIs

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/admin/oracle-configs` | List all Oracle configs |
| POST | `/api/admin/oracle-configs` | Add Oracle config |
| PUT | `/api/admin/oracle-configs/<id>` | Update Oracle config |
| DELETE | `/api/admin/oracle-configs/<id>` | Delete Oracle config |
| POST | `/api/admin/oracle-configs/<id>/test` | Test database connection |

### 5.4 Admin Alert Keywords APIs

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/admin/alert-keywords` | List all keywords by level |
| POST | `/api/admin/alert-keywords` | Add keyword |
| PUT | `/api/admin/alert-keywords/<id>` | Update keyword |
| DELETE | `/api/admin/alert-keywords/<id>` | Delete keyword |

### 5.5 Admin System Settings APIs

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/admin/settings` | Get all system settings |
| PUT | `/api/admin/settings` | Batch update settings |
| POST | `/api/admin/settings/reload` | Force reload config from DB (hot reload) |

### 5.6 Admin SSH Config APIs

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/admin/ssh-configs` | Get SSH configurations |
| PUT | `/api/admin/ssh-configs` | Update SSH configurations |

### 5.7 Admin Migration API

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/admin/migrate` | Run one-time migration from settings.py |
| GET | `/api/admin/migrate/status` | Check migration status |

### 5.8 Hot Reload Mechanism

When configuration is changed through the Admin Panel, the backend must reload the config in memory without restarting. Implementation approach:

1. Backend maintains a `ConfigManager` singleton that caches server configs in memory
2. All monitoring services read from `ConfigManager` instead of directly from `settings.py`
3. When Admin API updates the database, it calls `ConfigManager.reload()`
4. `ConfigManager.reload()` reads all `admin_*` tables and rebuilds the in-memory dicts
5. WebSocket broadcasts a `config_changed` event to frontend so Dashboard re-fetches server list

---

## 6. Page Layout & UI Design

### 6.1 Overall Layout

The Admin Panel maintains the cyberpunk/hacker aesthetic consistent with the Dashboard.

```
+------------------------------------------------------------------+
| [<< BACK TO DASHBOARD]    ADMIN PANEL // SYS-CONFIG    [v1.0]   |
+------------------------------------------------------------------+
|          |                                                        |
| NAV      |  CONTENT AREA                                         |
| MENU     |                                                        |
|          |  +--------------------------------------------------+  |
| [*] SRV  |  | Table / Form / Settings                         |  |
| [ ] SVC  |  |                                                  |  |
| [ ] DB   |  |                                                  |  |
| [ ] SSH  |  |                                                  |  |
| [ ] ALRT |  |                                                  |  |
| [ ] CMD  |  |                                                  |  |
| [ ] SYS  |  +--------------------------------------------------+  |
|          |                                                        |
+------------------------------------------------------------------+
| FOOTER: Last config update: 2026-02-10 09:00 | DB: acc_monitor  |
+------------------------------------------------------------------+
```

### 6.2 Left Navigation Menu

| Icon | Label | Route | Description |
|------|-------|-------|-------------|
| Server icon | SERVERS | `/admin/servers` | Server management |
| Gear icon | SERVICES | `/admin/services` | Service management (context: selected server) |
| Database icon | DATABASES | `/admin/databases` | Oracle config |
| Key icon | SSH | `/admin/ssh` | SSH credentials |
| Bell icon | ALERTS | `/admin/alerts` | Alert keyword rules |
| Terminal icon | COMMANDS | `/admin/commands` | Restart commands |
| Sliders icon | SYSTEM | `/admin/system` | System settings (intervals, thresholds) |

### 6.3 Color & Style Specifications

Consistent with existing cyberpunk theme:

| Element | Color | Note |
|---------|-------|------|
| Background | `#0a0a0a` to `#111111` | Dark terminal background |
| Primary text | `#00ffcc` (cyan) | Main text and labels |
| Secondary text | `#7a8a7a` | Descriptions, hints |
| Table header | `#1a2a1a` background | Dark green tint |
| Table row hover | `#0d1f0d` | Subtle green glow |
| Active nav item | `#00ff88` left border | Green accent |
| Button (primary) | `#00cc66` border, transparent bg | Outlined green |
| Button (danger) | `#ff3366` border | Red for delete actions |
| Toggle ON | `#00ff88` | Green |
| Toggle OFF | `#333333` | Gray |
| Input fields | `#1a1a1a` bg, `#00ffcc` border | Terminal input style |
| Success toast | `#00ff88` | Green notification |
| Error toast | `#ff3366` | Red notification |

### 6.4 Typography

- Font family: Same as Dashboard (monospace, e.g., 'JetBrains Mono', 'Fira Code', monospace)
- Headers: Uppercase with prefix markers (e.g., `> SERVER MANAGEMENT`)
- Table content: Regular monospace
- All labels use terminal-style formatting

### 6.5 Page-Level Wireframes

#### 6.5.1 Server List Page

```
> SERVER MANAGEMENT                                    [+ ADD SERVER]
-----------------------------------------------------------------------
| # | ID  | NAME              | DISPLAY | IP             | OS  | VIS | STATUS  | ACTIONS        |
|---|-----|-------------------|---------|----------------|-----|-----|---------|----------------|
| 1 | 153 | DP EPS Production | DP_EPS  | 172.17.10.153  | WIN | ON  | ONLINE  | [E] [S] [DEL]  |
| 2 | 164 | DP EPP Production | DP EPP  | 172.17.10.164  | WIN | ON  | ONLINE  | [E] [S] [DEL]  |
| 3 | 168 | SMT Line2 Prod    | SMT L2  | 172.17.10.168  | WIN | ON  | WARNING | [E] [S] [DEL]  |
| 4 | 193 | C EPS Production  | C_EPS   | 172.17.10.193  | WIN | ON  | ONLINE  | [E] [S] [DEL]  |
| 5 | 194 | L EPP Production  | L_EPP   | 172.17.10.194  | WIN | ON  | ONLINE  | [E] [S] [DEL]  |
| 6 | 160 | iPlant Server     | iPlant  | 172.17.10.160  | WIN | ON  | ONLINE  | [E] [S] [DEL]  |
| 7 | 163 | EAI Server        | EAI     | 172.17.10.163  | LNX | ON  | ONLINE  | [E] [S] [DEL]  |
| 8 | 165 | Common Services   | SHARED  | 172.17.10.165  | WIN | ON  | ONLINE  | [E] [S] [DEL]  |
-----------------------------------------------------------------------
                                                       [E]=Edit [S]=Services [DEL]=Delete

Drag rows to reorder. Changes are auto-saved.
```

#### 6.5.2 Add/Edit Server Modal

```
+------- ADD SERVER -----------------------------------------------+
|                                                                    |
|  $ SERVER_ID:  [________]    $ NAME:  [________________________]  |
|  $ DISPLAY:    [________]    $ IP:    [________________________]  |
|  $ OS_TYPE:    [Windows v]   $ DRIVE: [E ]  (Windows only)        |
|  $ LOG_PATH:   [E:\ACC\Log_______________________________]        |
|  $ HAS_ORACLE: [ON/OFF]     $ TYPE:  [Line DB v]                 |
|  $ SORT_ORDER: [9___]       $ VISIBLE: [ON/OFF]                  |
|                                                                    |
|                              [CANCEL]  [>> SAVE]                  |
+--------------------------------------------------------------------+
```

#### 6.5.3 Service Management Page (for a selected server)

```
> SERVICES // SERVER: DP_EPS (172.17.10.153)           [+ ADD SERVICE]
-----------------------------------------------------------------------
PROCESSES:
| # | Name   | Monitored | Visible | Actions   |
|---|--------|-----------|---------|-----------|
| 1 | Oracle | ON        | ON      | [E] [DEL] |

SERVICES (NSSM):
| # | Service Name                 | Display Name              | MON | VIS | AUTO-RST | ACTIONS   |
|---|------------------------------|---------------------------|-----|-----|----------|-----------|
| 1 | ACC.Server                   | ACC.Server                | ON  | ON  | OFF      | [E] [DEL] |
| 2 | ACC.MQ                       | ACC.MQ                    | ON  | ON  | OFF      | [E] [DEL] |
| 3 | ACC.PackServer               | Pack.Server               | ON  | ON  | OFF      | [E] [DEL] |
| 4 | ACC.LogReader                | ACC.LogReader             | ON  | ON  | OFF      | [E] [DEL] |
| 5 | HULU.EAI.Kingdee.Gateway     | HULU EAI Kingdee Gateway  | ON  | ON  | OFF      | [E] [DEL] |
-----------------------------------------------------------------------
[TOGGLE ALL MONITORED]  [TOGGLE ALL VISIBLE]
```

---

## 7. Technical Implementation Notes

### 7.1 Frontend Architecture

| Item | Technology |
|------|-----------|
| Framework | Vue 3 (existing) |
| State management | Pinia (existing) |
| Router | Vue Router (existing), add `/admin` routes |
| UI components | Custom cyberpunk components (reuse existing CyberModal, etc.) |
| HTTP client | Axios (existing) |
| Drag & drop | vuedraggable (new dependency, for server reordering) |

### 7.2 Backend Architecture

| Item | Technology |
|------|-----------|
| Framework | Flask (existing) |
| ORM | SQLAlchemy (existing) |
| Database | SQLite (existing acc_monitor.db) |
| Migration | Flask-Migrate / Alembic |
| New module | `backend/app/api/admin_routes.py` |
| New models | `backend/app/models/admin.py` |
| Config loader | `backend/app/services/config_manager.py` |

### 7.3 File Changes Summary

**New files**:
- `frontend/src/views/Admin.vue` - Admin panel main layout
- `frontend/src/views/admin/ServerList.vue` - Server management
- `frontend/src/views/admin/ServiceList.vue` - Service management
- `frontend/src/views/admin/DatabaseConfig.vue` - Oracle config
- `frontend/src/views/admin/AlertConfig.vue` - Alert keywords
- `frontend/src/views/admin/SystemSettings.vue` - System settings
- `frontend/src/views/admin/SSHConfig.vue` - SSH config
- `frontend/src/views/admin/CommandConfig.vue` - Restart commands
- `frontend/src/stores/admin.js` - Admin panel Pinia store
- `backend/app/api/admin_routes.py` - Admin REST API routes
- `backend/app/models/admin.py` - Admin database models
- `backend/app/services/config_manager.py` - Dynamic config loader
- `backend/migrations/add_admin_tables.py` - Migration script

**Modified files**:
- `frontend/src/router/index.js` - Add `/admin` routes
- `frontend/src/views/Dashboard.vue` - Add settings icon entry point
- `frontend/src/components/SystemLog.vue` - Add `admin` command support
- `backend/app/api/__init__.py` - Register admin blueprint
- `backend/app/services/monitor_service.py` - Read from ConfigManager
- `backend/app/services/database_service.py` - Read from ConfigManager
- `backend/config/settings.py` - Keep as fallback only

---

## 8. Acceptance Criteria

### 8.1 Server Management

- [ ] AC-01: Can add a new server with all required fields, server appears in admin list
- [ ] AC-02: Can edit any field of an existing server, changes persist after page refresh
- [ ] AC-03: Can soft-delete a server, server disappears from Dashboard but remains in admin list (marked as deleted)
- [ ] AC-04: Can toggle server visibility, hidden servers do not appear on Dashboard
- [ ] AC-05: Can reorder servers via drag-and-drop, order is reflected on Dashboard
- [ ] AC-06: IP address validation prevents invalid formats
- [ ] AC-07: Duplicate server ID is rejected with error message

### 8.2 Service Management

- [ ] AC-08: Can view all services/processes for a selected server
- [ ] AC-09: Can add a new service with service_name and display_name
- [ ] AC-10: Can toggle "monitored" flag, unmonitored services are not checked by backend
- [ ] AC-11: Can toggle "visible" flag, hidden services do not appear on server card
- [ ] AC-12: Can delete a service, it is removed from monitoring
- [ ] AC-13: Batch toggle all monitored/visible works correctly

### 8.3 Database Configuration

- [ ] AC-14: Can view all Oracle database configs
- [ ] AC-15: Can add/edit/delete Oracle config
- [ ] AC-16: "Test Connection" button returns success or detailed error message
- [ ] AC-17: Password is stored encrypted, not in plaintext

### 8.4 Alert Keywords

- [ ] AC-18: Can view keywords grouped by level
- [ ] AC-19: Can add/edit/delete keywords
- [ ] AC-20: New keywords are immediately effective in log scanning

### 8.5 System Settings

- [ ] AC-21: Can view and modify all threshold and interval values
- [ ] AC-22: Changes take effect without restarting the backend (hot reload)

### 8.6 Entry Point

- [ ] AC-23: Settings gear icon is visible on Dashboard top status bar
- [ ] AC-24: Clicking gear icon navigates to `/admin`
- [ ] AC-25: "BACK TO DASHBOARD" button returns to `/`
- [ ] AC-26: Typing `admin` or `config` in System Log terminal navigates to Admin Panel

### 8.7 General

- [ ] AC-27: All pages maintain cyberpunk visual style
- [ ] AC-28: All CRUD operations show success/error toast notifications
- [ ] AC-29: Config changes are hot-reloaded (no backend restart needed)
- [ ] AC-30: Migration script successfully imports all existing settings.py data
- [ ] AC-31: Backend falls back to settings.py if database tables are empty (Phase 1)

---

## 9. Priority & Phasing

### Phase 1 - MVP (Week 1-2)

**Must Have**:
- Entry point (gear icon on Dashboard)
- Server CRUD (add/edit/delete/toggle visibility)
- Service management per server (add/edit/delete/toggle)
- Database migration from settings.py
- Hot reload mechanism

### Phase 2 - Enhanced (Week 3)

**Should Have**:
- Server drag-and-drop reorder
- Oracle database configuration
- Alert keywords management
- System settings page

### Phase 3 - Polish (Week 4)

**Nice to Have**:
- SSH configuration management
- Restart commands configuration
- Terminal command entry (`admin` / `config`)
- Audit log (who changed what, when)
- Configuration import/export (JSON)

---

## 10. Risk Assessment

| Risk | Impact | Mitigation |
|------|--------|------------|
| Migration corrupts existing config | High | Backup settings.py before migration; keep fallback logic |
| Hot reload causes service interruption | Medium | Implement graceful reload with mutex locks |
| Concurrent edits from multiple users | Low | SQLite handles single-writer; add optimistic locking |
| Password storage security | Medium | Use Fernet symmetric encryption for DB passwords |
| Large config file causes slow load | Low | Current scale (8 servers) is trivial; add caching |

---

## 11. Dependencies

| Dependency | Owner | Status |
|-----------|-------|--------|
| Backend API development | @Cheng Yuan | Not started |
| Frontend page development | @Cheng Yuan | Not started |
| UI design (cyberpunk components) | @Lin Xi | Not started |
| Database migration testing | @Han Master | Not started |

---

## 12. Open Questions

| # | Question | Decision Needed By |
|---|----------|-------------------|
| 1 | Do we need authentication/login for the Admin Panel? (Currently no auth on any page) | Boss |
| 2 | Should deleted servers' historical monitoring data be preserved? | Boss |
| 3 | Maximum number of servers the system should support? | Product/Tech |
| 4 | Should we support bulk import of servers from CSV/JSON? | Phase 3 consideration |

---

## Appendix A: Current SERVERS Data Structure Reference

```python
SERVERS = {
    '<server_id>': {
        'name': str,          # English name
        'name_cn': str,       # Short display name
        'ip': str,            # IPv4 address
        'os': str,            # 'windows' or 'linux'
        'acc_drive': str,     # Drive letter (Windows only)
        'log_path': str,      # Log directory path
        'processes': list,    # ['Oracle', ...] - process names to monitor
        'services': list,     # [{'service_name': str, 'display_name': str}, ...]
        'containers': list,   # ['hulu-eai', 'redis'] (Linux only)
        'container_metrics': bool,  # Enable container resource monitoring (Linux only)
        'monitored_metrics': list,  # [{'container': str, 'metric': str, 'display_name': str}]
        'has_oracle': bool,
        'oracle_type': str,   # 'line' or 'factory' (optional)
        'sort_order': int
    }
}
```

## Appendix B: Glossary

| Term | Definition |
|------|-----------|
| ACC | Automated Control Center - the main production system |
| NSSM | Non-Sucking Service Manager - Windows service wrapper |
| EAI | Enterprise Application Integration |
| Dashboard | Main monitoring view showing all server cards |
| Server Card | Individual server status panel on Dashboard |
| Hot Reload | Applying configuration changes without restarting the service |
| Cyberpunk Theme | Dark background with neon cyan/green terminal-style UI |

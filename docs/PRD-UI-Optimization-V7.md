# ACC Monitor UI Optimization PRD - V7

> Author: Su Jin (Product Director)
> Date: 2026-02-09
> Status: Draft
> Related Project: D:\TechTeam\Projects\ACC-Monitor\

---

## 1. Background and Objective

The boss reviewed the current ACC Monitor Dashboard (cyberpunk/hacker-style monitoring panel) and raised 3 UI optimization requirements. This document provides a product-level analysis, functional specification, and acceptance criteria for each requirement.

**Current Interface Layout:**
- Top: Status bar (server count, LIVE indicator, uptime, ping)
- Left main area (70%): Server rack cabinet with 8 server cards in 4x2 grid
- Right sidebar (30%): Upper section = PixelFace (hacker guardian image), Lower section = SystemLog panel
- Full-screen background: Multi-layer matrix rain (BackgroundEffects component)

---

## 2. Requirement Analysis

### 2.1 REQ-01: Matrix Rain Background Obscured by Foreground Elements

**Problem Analysis:**

The background matrix rain effect is implemented in `D:\TechTeam\Projects\ACC-Monitor\frontend\src\components\BackgroundEffects.vue` with three canvas layers (bg/mid/fg) at z-index 2-4. The main content in `Dashboard.vue` sits at z-index 10. While the dashboard container and main-content are set to `background: transparent`, the server rack cabinet area (`servers-section`) has a semi-transparent background with `rgba(15, 18, 22, 0.72)` as its primary fill, plus `backdrop-filter: blur(8px)`. The right sidebar components (PixelFace with `rgba(0, 10, 20, 0.85)` and SystemLog with `rgba(8, 10, 14, 0.62)`) also have their own opaque backgrounds.

The combined effect is:
1. The server rack cabinet covers approximately 70% of the screen with 68-72% opacity background plus blur -- this almost completely blocks the matrix rain.
2. The `::before` and `::after` pseudo-elements on `servers-section` use 92-95% opacity backgrounds for the top/bottom cabinet panels.
3. The inner rack structure (`servers-grid::before`) has 0.95 opacity metal gradients on left/right rails.
4. Right side: PixelFace at 85-90% opacity, SystemLog at 62% opacity with blur.
5. The `gradient-overlay` in BackgroundEffects adds additional darkening via radial gradient at z-index 8.
6. The `top-status-bar` has `rgba(0, 0, 0, 0.38)` plus `backdrop-filter: blur(8px)`.

In total, approximately 95% of the visible screen area is covered by elements that significantly attenuate or fully block the matrix rain.

**Root Cause:** The matrix rain visibility was treated as a secondary concern. Each UI component independently chose its own background opacity for readability, resulting in cumulative coverage that defeats the purpose of the background effect.

**Functional Specification:**

| Item | Specification |
|------|---------------|
| Goal | Matrix rain should be clearly visible through and around all foreground elements |
| Approach A - Transparency Enhancement | Reduce opacity of all foreground backgrounds by 20-30%. Server rack: 0.72 -> 0.45-0.50. Top bar: 0.38 -> 0.25. SystemLog: 0.62 -> 0.40-0.45. Cabinet top/bottom panels: 0.92-0.95 -> 0.70-0.75 |
| Approach B - Layout Gap Strategy | Add visible gaps/margins between server cards and around the rack where matrix rain shows through unobstructed. Increase grid gap from 28px to 36-40px. Reduce rack padding to expose more background |
| Approach C - Mixed Transparency (Recommended) | Use variable transparency: card centers at 50-55% opacity for readability, edges fade to 20-30% opacity to blend into matrix rain. Use CSS mask-image gradient on server-section to soften edges |
| Blur Adjustment | Reduce backdrop-filter blur from 8px to 3-4px. Excessive blur erases fine matrix rain detail |
| Cabinet Decoration Opacity | Reduce cabinet rails, screws, top/bottom panels to 50-60% opacity. These decorative elements currently use 85-95% and unnecessarily block the background |
| Matrix Rain Layer Boost | Increase foreground matrix layer opacity from 0.9 to 1.0. Increase brightness filter from 1.2 to 1.4. Ensure canvas z-index allows some characters to render above the gradient-overlay |
| Text Readability | Ensure all critical data (server name, IP, status, CPU/MEM percentages) remain legible. Use text-shadow with darker backing for contrast instead of relying on opaque card backgrounds |

**Acceptance Criteria:**

- [ ] AC-01: Matrix rain characters are visible in at least 3 distinct areas: (1) gaps between server cards, (2) faintly through the server rack background, (3) in the top-bar area
- [ ] AC-02: All server card data (name, IP, status, processes) remains readable without squinting
- [ ] AC-03: The overall visual impression is "data rain falling through transparent panels" not "opaque panels on a black background"
- [ ] AC-04: Matrix rain is visible through the sidebar (PixelFace and SystemLog areas) at reduced but noticeable intensity
- [ ] AC-05: No performance regression (matrix canvas rendering remains smooth at current frame rates: bg=12fps, mid=20fps, fg=30fps)

---

### 2.2 REQ-02: System Log Displays Simulated Data Instead of Real Logs

**Problem Analysis:**

This is the most technically involved of the three requirements. Let me trace the complete data flow:

**Backend Data Pipeline (Current State):**

1. **LogService** (`D:\TechTeam\Projects\ACC-Monitor\backend\app\services\log_service.py`):
   - `SystemLogBuffer`: Singleton in-memory circular buffer (deque, maxlen=100) storing log entries.
   - `add_system_log()`: Creates log entries with `{time, timestamp, level, server_id, message}`.
   - `get_recent_logs()` / `_get_windows_logs()`: These methods are designed to read actual server log files (e.g., `E:\iPlant.ACC\Log\ACC.Server.log`), but they currently return **simulated strings**: `"[Simulated log content for {process_name} on server {server_id}]"` (line 127). The Linux variant uses SSH (`paramiko`) and does attempt real reads.
   - `get_device_logs()`: Returns empty list `[]` (line 187) -- not implemented.
   - `scan_for_alerts()`: Scans log content for keywords, but since `get_recent_logs()` returns simulated data for Windows servers, this scan produces no meaningful results for 7 of 8 servers.

2. **Scheduler** (`D:\TechTeam\Projects\ACC-Monitor\backend\app\utils\scheduler.py`):
   - `_check_processes()`: Every 30 seconds, checks processes. When a process is stopped, it calls `log_service.add_system_log()` and `broadcast_system_log()` -- these are REAL monitoring events.
   - `_check_databases()`: Every 5 minutes, checks tablespace usage. Broadcasts real warnings via system log.
   - `_scan_logs()`: Every 60 seconds, calls `log_service.scan_for_alerts()` -- but as noted above, Windows log reading returns simulated data, so this mostly yields nothing.
   - `_log_health_status()`: Every 60 seconds, generates a health summary like "All 8 servers healthy" or "Health check: 5 online, 3 offline". This IS a real log.
   - `_probe_offline_servers()`: Every 15 seconds, probes offline servers and generates recovery logs -- real data.

3. **WebSocket** (`D:\TechTeam\Projects\ACC-Monitor\backend\app\api\websocket.py`):
   - On client connect: sends `system_logs_batch` with last 20 logs from buffer.
   - `broadcast_system_log()`: Pushes individual log entries to all clients in real-time.
   - `handle_system_logs_request()`: Client can request up to 50 logs on demand.

4. **Agent Report API** (`D:\TechTeam\Projects\ACC-Monitor\backend\app\api\routes.py`):
   - `/api/agent/report` (POST): Receives metrics from monitoring agents deployed on each server. Processes alerts from agent data, but does NOT write these to the system log buffer.

**Frontend Data Pipeline (Current State):**

5. **WebSocket Composable** (`D:\TechTeam\Projects\ACC-Monitor\frontend\src\composables\useWebSocket.js`):
   - Listens for `systemLog` and `systemLogsBatch` events.
   - Calls `monitorStore.addSystemLog()` / `monitorStore.setSystemLogs()`.

6. **Monitor Store** (`D:\TechTeam\Projects\ACC-Monitor\frontend\src\stores\monitor.js`):
   - `systemLogs` ref: Stores up to 50 log entries.
   - `addSystemLog()`: Prepends new log. `setSystemLogs()`: Replaces all logs (batch load).

7. **Dashboard.vue** (`D:\TechTeam\Projects\ACC-Monitor\frontend\src\views\Dashboard.vue`):
   - `systemLogs` computed: First tries `monitorStore.systemLogs`, then falls back to `monitorStore.alerts`, then returns empty array.
   - Passes logs to `<SystemLog :logs="systemLogs" :max-entries="8" />`.

8. **SystemLog.vue** (`D:\TechTeam\Projects\ACC-Monitor\frontend\src\components\SystemLog.vue`):
   - Has hardcoded `defaultLogs` (lines 83-92): 8 fake entries like "IPS_EPS: Connection timeout detected", "SMT_EPS: High CPU usage (78%)", "DP_EPS: Service health check passed", etc.
   - `displayLogs` computed: Uses `props.logs` if non-empty, otherwise falls back to `defaultLogs`.
   - The typewriter animation plays on the first log entry when new ones arrive.

**Why Fake Data Appears:**

The problem is a **cascade of fallbacks**:
1. If the WebSocket connection is not established (or the backend is not running), `monitorStore.systemLogs` stays empty.
2. If `systemLogs` is empty and `monitorStore.alerts` is also empty, Dashboard.vue returns `[]`.
3. SystemLog.vue receives empty array -> falls back to hardcoded `defaultLogs` -> user sees fake data.

Even when the backend IS running, the system log buffer only receives entries from:
- Process check failures (every 30s, but only if a process is stopped)
- Database warnings (every 5min, but only if tablespace is high)
- Health status summaries (every 60s -- this is the most reliable real data source)
- Server recovery/offline events (intermittent)
- Startup messages (3 entries: "System monitoring initialized", "WebSocket server ready", "Connecting to servers...")

So in a normal healthy state, the buffer only gets a health status message every 60 seconds. Between those, the display could stall and appear stale.

**Real Log Data Sources Available:**

| Source | Location | Type | Richness |
|--------|----------|------|----------|
| ACC Application Logs | `{acc_drive}:\iPlant.ACC\Log\ACC.Server.log` (per server) | Text files on remote Windows servers | High - real application events, errors, transactions |
| Oracle Alert Logs | Oracle alert log directory on each server | Database logs | Medium - DB events, ORA errors |
| Device/Station Logs | `{log_path}\Device\` subdirectory | Equipment logs | Medium - station-specific events |
| Linux Container Logs | `/var/eai/logs/` on server 163 | Docker logs | Medium - container events |
| Agent Reports | In-memory via agent_data_service | API push from agents | High - real-time metrics, alerts |
| Monitoring Events | Scheduler-generated | In-memory | Medium - process checks, health status |
| Windows Event Log | Windows Event Viewer on each server | System events | Medium - system-level events |

**Functional Specification:**

| Item | Specification |
|------|---------------|
| Goal | SystemLog panel displays only real, meaningful monitoring data. No fake/demo data. |
| Remove Default Logs | Delete `defaultLogs` from SystemLog.vue. When no logs exist, show a "Waiting for data..." message with blinking cursor |
| Fix Windows Log Reading | Implement actual WinRM/SSH-based log reading in `_get_windows_logs()`. Replace the simulated return string with real PowerShell remote execution via `pywinrm` or SSH |
| Enrich System Log Sources | Add more event types to the system log buffer beyond just process failures and health checks |
| Agent Alert Integration | When `/api/agent/report` receives alerts from agents, write them to `system_log_buffer` and broadcast via WebSocket. Currently agent alerts are stored in DB but NOT shown in system log panel |
| Process Status Logging | Log ALL process check results (not just stopped processes). Add info-level logs like "DP_EPS: 5/5 processes running" for normal checks. This provides continuous data flow |
| Connection Events | Log server connection/disconnection events to system log buffer (some of this exists in scheduler._probe_offline_servers but can be expanded) |
| Resource Threshold Logging | When CPU > 70%, Memory > 80%, or Disk > 85%, generate warning-level system logs even if no process is stopped |
| Log Freshness | System log should have at least 1 new entry every 30 seconds during normal operation. The health check interval (currently 60s) should be reduced to 30s, or process check results should always generate a log entry |
| Startup Behavior | On initial WebSocket connection, client receives the last 20 real logs from buffer. If buffer has < 3 entries (fresh start), display "System initializing..." state |
| Log Source Tag | Each log entry should include the source/origin (e.g., "PROCESS_CHECK", "DB_CHECK", "AGENT", "HEALTH", "LOG_SCAN") so users can quickly identify log type |

**Acceptance Criteria:**

- [ ] AC-06: SystemLog panel shows ONLY data originating from real server monitoring events. Zero hardcoded/demo entries.
- [ ] AC-07: When backend is running and servers are monitored, at least 1 new log entry appears every 30 seconds
- [ ] AC-08: Log entries show real server names (DP_EPS, C_EPS, SMT Line2, etc.) and real events (process status, resource alerts, DB status)
- [ ] AC-09: When backend is not reachable, panel shows "CONNECTION LOST" state instead of fake data
- [ ] AC-10: Agent-reported alerts appear in the SystemLog within 5 seconds of receipt
- [ ] AC-11: Log entries display correctly with the existing typewriter animation for new entries
- [ ] AC-12: Historical logs (last 20) are loaded on page refresh via WebSocket `system_logs_batch` event

---

### 2.3 REQ-03: Hacker Guardian Image Needs Magic/Phantom Effects

**Problem Analysis:**

The current PixelFace component (`D:\TechTeam\Projects\ACC-Monitor\frontend\src\components\PixelFace.vue`) displays a static PNG image (`hacker-guardian.png`) with the following effects:
- Container: Dark blue-green gradient background (85-90% opacity)
- Glow: Radial gradient behind image with breathing animation (3s cycle)
- CRT Signal: `crtSignal` keyframe animation that runs on a 5s cycle. For the first 89% of the cycle, it only varies brightness and glow intensity slightly. In the last 11% (frames 89%-97%), it does rapid opacity drops (to 0.5-0.85) with contrast spikes and brief red/cyan color shift -- simulating a signal burst.
- Noise: SVG fractal noise overlay at 10-15% opacity with flicker animation
- Scanline: A horizontal line sweeping top to bottom every 3s
- Eye blink: Small overlay rectangles that simulate eye closing at 94-98% of a 4s cycle
- Mouth animation: Overlay that simulates talking (rapid open/close at 0.8s cycle)

**What's Missing (Boss's Requirements):**

The boss wants the character to feel more "magical" and "phantom-like" with these specific effects:
1. **Intermittent appearance/disappearance** - The image should sometimes fade to near-invisible and then materialize back. Currently it only drops to opacity 0.5 briefly.
2. **Fragmentation/particle effect** - The image should sometimes appear to break into fragments/particles and reassemble. This is not present at all.
3. **Signal interference/glitch** - More dramatic glitch effects: horizontal line displacement, RGB channel splitting, static noise bursts. The current effect is very subtle and only covers 11% of the animation cycle.

**Functional Specification:**

| Item | Specification |
|------|---------------|
| Goal | The guardian image has a mysterious, phantom-like presence that feels alive and magical |
| Disappearance Cycle | Every 8-15 seconds (randomized), the image should fade to opacity 0 over 0.3-0.5s, remain invisible for 1-3s, then materialize back over 0.5-1.0s. The return should have a "hologram flicker" effect (rapid opacity oscillation 0->0.3->0->0.6->0->1.0) |
| Fragmentation Effect | Implement using CSS clip-path with multiple polygon regions, or use a canvas-based particle dissolve. The image breaks into 8-16 horizontal slices that shift left/right independently before snapping back together. Frequency: every 15-25 seconds, duration: 0.5-1.5s |
| Glitch Intensification | Increase glitch frequency from current 11% of cycle to at least 25%. Add RGB channel split (red shadow offset left, cyan shadow offset right) during glitch frames. Add horizontal scanline displacement (random rows of the image shift 5-15px left/right) |
| Digital Static Burst | Periodically (every 20-30s), overlay the image with a full white noise/static pattern at 40-60% opacity for 0.1-0.3s, simulating a "signal lost" moment |
| Holographic Shimmer | Add a subtle continuous holographic rainbow shimmer at the edges of the image (using CSS hue-rotate animation on a gradient overlay). This creates an "otherworldly" quality |
| State Responsiveness | When a server goes critical (status: error), the guardian's glitch effects should intensify (faster, more dramatic). When all servers are healthy, effects should be calmer |
| Performance | All effects must run smoothly without jank. Prefer CSS animations over JavaScript for continuous effects. Canvas-based particle effects (if used) should be capped at 15fps |

**Technical Implementation Approach:**

The recommended approach combines CSS and lightweight JavaScript:
- **Disappearance**: CSS animation with `animation-delay` randomized via JS. Use `opacity` and `filter: blur()` transitions.
- **Fragmentation**: CSS `clip-path` with `inset()` applied to multiple overlay copies of the image, each slice offset via `transform: translateX()`. Controlled by a JS interval that toggles a CSS class.
- **Glitch**: Extend the existing `crtSignal` keyframes. Add `::before` and `::after` pseudo-elements on `.guardian-wrapper` for RGB split (each colored with `mix-blend-mode`).
- **Static Burst**: Canvas overlay with random pixel noise, toggled by JS interval.

**Acceptance Criteria:**

- [ ] AC-13: The guardian image visibly disappears and reappears at least once every 15 seconds
- [ ] AC-14: The disappearance is not a simple fade -- it includes at least one of: fragmentation, static burst, or holographic flicker
- [ ] AC-15: RGB channel split (red/cyan offset) is visible during glitch moments
- [ ] AC-16: The image appears to "break apart" into horizontal slices at least once every 30 seconds
- [ ] AC-17: A brief static/noise burst (full image covered) occurs at least once per minute
- [ ] AC-18: Effects do not cause noticeable frame drops or jank (smooth animation)
- [ ] AC-19: The effect intensity visually increases when any server is in error/critical state
- [ ] AC-20: The overall impression is "mysterious digital phantom" not "broken display"

---

## 3. Priority Ranking

| Priority | Requirement | Rationale |
|----------|-------------|-----------|
| **P0 - Critical** | REQ-02: Real System Log | This is a functional defect: the panel shows fake data. Users cannot rely on SystemLog for monitoring, defeating its core purpose. Must fix first. |
| **P1 - High** | REQ-01: Matrix Rain Visibility | This is a visual design defect affecting the overall aesthetic identity of the product. The cyberpunk theme loses its signature element. Important but less urgent than data correctness. |
| **P2 - Medium** | REQ-03: Guardian Phantom Effects | This is a visual enhancement. The current guardian already has basic effects. Enhancing to "magical phantom" level is desirable but not blocking any functionality. |

**Recommended Execution Order:**

```
Phase 1 (REQ-02): Backend log pipeline fix + frontend fallback removal
  Estimated effort: 1-2 days
  Dependencies: Backend changes needed first, then frontend
  Assigned to: @ChenYuan (backend log pipeline) + @LinXi (frontend SystemLog component)

Phase 2 (REQ-01): Matrix rain transparency optimization
  Estimated effort: 0.5-1 day
  Dependencies: Pure frontend CSS changes
  Assigned to: @LinXi (CSS transparency tuning)

Phase 3 (REQ-03): Guardian phantom effects
  Estimated effort: 1-1.5 days
  Dependencies: Pure frontend, independent of other changes
  Assigned to: @LinXi (CSS/JS animation implementation)
```

---

## 4. Technical Feasibility Notes

### REQ-02 - Key Technical Considerations

1. **Windows Remote Log Reading**: The current `_get_windows_logs()` returns simulated data. Implementing real log reading requires one of:
   - **WinRM** (pywinrm): Execute PowerShell `Get-Content -Tail` remotely. Requires WinRM service enabled on each server and firewall rules.
   - **SSH** (paramiko via OpenSSH for Windows): Already used for Linux server 163. Could be extended if OpenSSH is installed on Windows servers.
   - **Agent-Based** (Recommended): The monitoring agents already run on each server. Extend agents to include recent log lines in their periodic reports via `/api/agent/report`. This avoids additional remote access configuration.

2. **Log Volume**: With 8 servers generating logs every 30s, the buffer can fill quickly. The current maxlen=100 is appropriate. Consider adding a `level` filter so the dashboard only shows warning+ by default.

3. **WebSocket Reliability**: If WebSocket disconnects, the frontend should not fall back to fake data. It should show a "reconnecting..." state.

### REQ-01 - Key Technical Considerations

1. **Readability vs Transparency Trade-off**: Reducing card background opacity requires compensating with text-shadow or text backdrop for readability. Testing on actual monitoring data is essential.
2. **backdrop-filter Performance**: Reducing blur radius improves both transparency and performance.

### REQ-03 - Key Technical Considerations

1. **clip-path Animation Performance**: `clip-path` changes trigger repaints. For smooth fragmentation, limit to 8-12 slices and use `will-change: clip-path`.
2. **Canvas vs CSS**: CSS-only approach preferred for maintainability. Canvas only needed if particle dissolve effect is required.

---

## 5. File Reference

| File | Role | Modifications Needed |
|------|------|---------------------|
| `D:\TechTeam\Projects\ACC-Monitor\backend\app\services\log_service.py` | Backend log service | Fix `_get_windows_logs()`, enrich log sources |
| `D:\TechTeam\Projects\ACC-Monitor\backend\app\utils\scheduler.py` | Background scheduler | Add process status info-logs, reduce health check interval |
| `D:\TechTeam\Projects\ACC-Monitor\backend\app\api\routes.py` | REST API routes | Add agent alert -> system log integration |
| `D:\TechTeam\Projects\ACC-Monitor\backend\app\api\websocket.py` | WebSocket handlers | No major changes needed |
| `D:\TechTeam\Projects\ACC-Monitor\backend\config\settings.py` | Configuration | Add resource threshold settings |
| `D:\TechTeam\Projects\ACC-Monitor\frontend\src\components\SystemLog.vue` | System log display | Remove `defaultLogs`, add empty/error states |
| `D:\TechTeam\Projects\ACC-Monitor\frontend\src\views\Dashboard.vue` | Main dashboard | Update systemLogs fallback logic |
| `D:\TechTeam\Projects\ACC-Monitor\frontend\src\components\BackgroundEffects.vue` | Matrix rain background | Boost opacity/brightness values |
| `D:\TechTeam\Projects\ACC-Monitor\frontend\src\components\PixelFace.vue` | Guardian image | Complete rewrite of animation system |
| `D:\TechTeam\Projects\ACC-Monitor\frontend\src\stores\monitor.js` | State management | No major changes needed |

---

## 6. Self-Check

- [x] Requirement background is clear (boss review feedback on 3 specific UI issues)
- [x] User scenarios are defined (monitoring personnel viewing dashboard in real-time)
- [x] Feature points are complete (3 requirements fully specified)
- [x] Acceptance criteria are specific and testable (20 acceptance criteria defined)
- [x] Technical feasibility is assessed (notes provided for each requirement)
- [x] Document structure is clear
- [x] Priority ranking with rationale provided
- [x] Aligned with technical implementation reality (code analysis performed)

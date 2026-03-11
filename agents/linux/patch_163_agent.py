#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Patch acc_agent_163.py on server 163:
Change from error-level-only grep to ALL-levels grep (date filter only).
Now collects all log lines from today regardless of level.
Backend will extract the real level from the log message content.

Python 3.6 compatible (CentOS 7).
"""
import sys

AGENT_FILE = '/opt/acc-monitor-agent/acc_agent_163.py'


def main():
    with open(AGENT_FILE, 'r') as f:
        content = f.read()

    patched = False

    # === Patch 1: get_container_error_logs - remove level-tag grep, just tail ===
    old_container_cmd = (
        "'grep -E \"\\\\[ERRO\\\\]|\\\\[ERROR\\\\]|\\\\[FATAL\\\\]|\\\\[CRITICAL\\\\]\" | tail -20'"
    )
    new_container_cmd = "'tail -50'"

    if old_container_cmd in content:
        content = content.replace(old_container_cmd, new_container_cmd)
        print("[PATCH 1] get_container_error_logs: removed level grep, now collects all lines")
        patched = True
    else:
        print("[SKIP 1] get_container_error_logs: old pattern not found")

    # === Patch 2: scan_recent_logs - replace entire function ===
    old_scan = '''    def scan_recent_logs(self, minutes=5):
        """Scan recent log files for errors (today only).

        EAI log format: [LEVEL][YYYY-MM-DD HH:MM:SS.mmm][source][...] content
        We only match lines whose LEVEL tag is [ERRO], [ERROR], [FATAL], or [CRITICAL].
        This avoids false positives from [INFO] lines that happen to contain
        the word 'error' in their message body.
        """
        alerts = []
        log_path = self.config.get("log_path", "/var/eai/logs")
        if not os.path.exists(log_path):
            return alerts
        cutoff_time = time.time() - (minutes * 60)
        today_str = datetime.now().strftime("%Y-%m-%d")
        try:
            import glob as g
            for log_file in g.glob(os.path.join(log_path, "*.log")):
                if os.path.getmtime(log_file) < cutoff_time:
                    continue
                # grep for today's date AND error-level tags in the log header
                # EAI uses [ERRO] (4-char) or [ERROR] (5-char), plus [FATAL]/[CRITICAL]
                cmd = (
                    'grep "%s" "%s" | '
                    'grep -E "\\\\[ERRO\\\\]|\\\\[ERROR\\\\]|\\\\[FATAL\\\\]|\\\\[CRITICAL\\\\]" | '
                    'tail -20'
                ) % (today_str, log_file)
                output = self.run_command(cmd)
                if output:
                    for line in output.split("\\n"):
                        line = line.strip()
                        if not line:
                            continue
                        alerts.append({
                            "file": os.path.basename(log_file),
                            "keyword": "ERROR",
                            "message": line[:200],
                            "timestamp": datetime.now().isoformat()
                        })
        except Exception as e:
            logger.error("Error scanning logs: %s", e)
        return alerts'''

    new_scan = '''    def scan_recent_logs(self, minutes=5):
        """Scan recent log files for today's logs (all levels).

        EAI log format: [LEVEL][YYYY-MM-DD HH:MM:SS.mmm][source][...] content
        We collect all log lines from today (INFO/WARN/ERRO/ERROR/FATAL/CRITICAL)
        so the dashboard can display them with proper level coloring.
        Only date filtering is applied here; no level filtering.
        """
        alerts = []
        log_path = self.config.get("log_path", "/var/eai/logs")
        if not os.path.exists(log_path):
            return alerts
        cutoff_time = time.time() - (minutes * 60)
        today_str = datetime.now().strftime("%Y-%m-%d")
        try:
            import glob as g
            for log_file in g.glob(os.path.join(log_path, "*.log")):
                if os.path.getmtime(log_file) < cutoff_time:
                    continue
                # grep for today's date only - collect ALL levels
                cmd = 'grep "%s" "%s" | tail -50' % (today_str, log_file)
                output = self.run_command(cmd)
                if output:
                    for line in output.split("\\n"):
                        line = line.strip()
                        if not line:
                            continue
                        alerts.append({
                            "file": os.path.basename(log_file),
                            "keyword": "LOG",
                            "message": line[:200],
                            "timestamp": datetime.now().isoformat()
                        })
        except Exception as e:
            logger.error("Error scanning logs: %s", e)
        return alerts'''

    if old_scan in content:
        content = content.replace(old_scan, new_scan)
        print("[PATCH 2] scan_recent_logs: replaced with all-levels version")
        patched = True
    else:
        print("[SKIP 2] scan_recent_logs: old function not found exactly")

    if not patched:
        print("[ERROR] No patches applied. Manual review needed.")
        sys.exit(1)

    # Write the patched file
    with open(AGENT_FILE, 'w') as f:
        f.write(content)

    print("[DONE] Agent file patched: %s" % AGENT_FILE)


if __name__ == '__main__':
    main()

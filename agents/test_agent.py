# -*- coding: utf-8 -*-
"""
ACC Monitor - Test Agent
Simulates agent behavior for local testing without real server connection

Usage:
    python test_agent.py [--server-id=164] [--url=http://localhost:5000]
"""
import sys
import time
import json
import random
import socket
import argparse
import requests
from datetime import datetime


def generate_test_metrics(server_id: str, scenario: str = 'normal') -> dict:
    """
    Generate test metrics data

    Scenarios:
        - normal: All processes running, normal resource usage
        - warning: High resource usage
        - error: Some processes stopped
        - mixed: Random mix of states
    """
    processes_config = {
        '164': ['Pack.Server', 'ACC.Server', 'ACC.MQ', 'ACC.Packing', 'Oracle'],
        '168': ['Pack.Server', 'ACC.Server', 'ACC.MQ', 'ACC.LogReader', 'Oracle'],
        '153': ['Pack.Server', 'ACC.Server', 'ACC.MQ', 'ACC.LogReader', 'Oracle'],
        '193': ['ACC.Server', 'ACC.MQ', 'ACC.LogReader', 'Oracle'],
        '194': ['ACC.Server', 'ACC.MQ', 'ACC.LogReader', 'Oracle'],
        '165': ['Oracle'],
    }

    process_names = processes_config.get(server_id, ['Pack.Server', 'ACC.Server', 'Oracle'])

    # Generate resource data based on scenario
    if scenario == 'normal':
        cpu = random.uniform(10, 40)
        memory = random.uniform(30, 60)
        disk = random.uniform(40, 70)
    elif scenario == 'warning':
        cpu = random.uniform(80, 95)
        memory = random.uniform(85, 95)
        disk = random.uniform(75, 88)
    elif scenario == 'error':
        cpu = random.uniform(20, 50)
        memory = random.uniform(40, 70)
        disk = random.uniform(50, 75)
    else:  # mixed
        cpu = random.uniform(10, 90)
        memory = random.uniform(20, 90)
        disk = random.uniform(30, 85)

    # Generate process status
    processes = []
    for proc_name in process_names:
        if scenario == 'normal':
            status = 'running'
        elif scenario == 'error':
            # 30% chance of stopped
            status = 'stopped' if random.random() < 0.3 else 'running'
        elif scenario == 'mixed':
            status = random.choice(['running', 'running', 'running', 'stopped'])
        else:
            status = 'running'

        processes.append({
            'name': proc_name,
            'status': status,
            'pid': random.randint(1000, 9999) if status == 'running' else 0,
            'cpu': round(random.uniform(0.5, 15.0), 2) if status == 'running' else 0,
            'memory': round(random.uniform(50, 500), 2) if status == 'running' else 0,
            'uptime': random.randint(3600, 86400 * 7) if status == 'running' else 0
        })

    # Generate alerts for error scenario
    alerts = []
    if scenario == 'error':
        alerts.append({
            'file': 'ACC.Server.log',
            'keyword': 'Error',
            'message': f'Connection timeout at {datetime.now().isoformat()}',
            'timestamp': datetime.now().isoformat()
        })

    return {
        'server_id': server_id,
        'hostname': f'SRV-{server_id}',
        'timestamp': datetime.utcnow().isoformat(),
        'resources': {
            'cpu_usage': round(cpu, 2),
            'memory_usage': round(memory, 2),
            'disk_usage': round(disk, 2)
        },
        'processes': processes,
        'alerts': alerts
    }


def send_report(url: str, metrics: dict) -> bool:
    """Send metrics to monitoring center"""
    try:
        response = requests.post(
            f"{url}/api/agent/report",
            json=metrics,
            headers={'Content-Type': 'application/json'},
            timeout=10
        )
        response.raise_for_status()
        return True
    except requests.exceptions.RequestException as e:
        print(f"Error sending report: {e}")
        return False


def run_test_agent(server_id: str, url: str, interval: int = 10, scenario: str = 'normal'):
    """Run test agent loop"""
    print("=" * 60)
    print("ACC Monitor - Test Agent")
    print("=" * 60)
    print(f"Server ID: {server_id}")
    print(f"Monitor URL: {url}")
    print(f"Interval: {interval}s")
    print(f"Scenario: {scenario}")
    print("=" * 60)
    print("Press Ctrl+C to stop\n")

    while True:
        try:
            metrics = generate_test_metrics(server_id, scenario)

            # Print summary
            procs = metrics['processes']
            running = sum(1 for p in procs if p['status'] == 'running')
            stopped = sum(1 for p in procs if p['status'] == 'stopped')

            print(f"[{datetime.now().strftime('%H:%M:%S')}] "
                  f"CPU: {metrics['resources']['cpu_usage']:.1f}% | "
                  f"Mem: {metrics['resources']['memory_usage']:.1f}% | "
                  f"Disk: {metrics['resources']['disk_usage']:.1f}% | "
                  f"Processes: {running} up, {stopped} down")

            success = send_report(url, metrics)
            if success:
                print(f"  -> Report sent successfully")
            else:
                print(f"  -> Failed to send report")

        except Exception as e:
            print(f"Error: {e}")

        time.sleep(interval)


def main():
    parser = argparse.ArgumentParser(description='ACC Monitor Test Agent')
    parser.add_argument('--server-id', '-s', default='164',
                        help='Server ID to simulate (default: 164)')
    parser.add_argument('--url', '-u', default='http://localhost:5000',
                        help='Monitor center URL (default: http://localhost:5000)')
    parser.add_argument('--interval', '-i', type=int, default=10,
                        help='Report interval in seconds (default: 10)')
    parser.add_argument('--scenario', '-c', default='normal',
                        choices=['normal', 'warning', 'error', 'mixed'],
                        help='Test scenario (default: normal)')

    args = parser.parse_args()

    try:
        run_test_agent(args.server_id, args.url, args.interval, args.scenario)
    except KeyboardInterrupt:
        print("\nTest agent stopped")


if __name__ == '__main__':
    main()

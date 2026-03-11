#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ACC Monitor - Linux Agent (163 EAI Server Edition)
Compatible with Python 3.6.8 (CentOS 7)

Collects server metrics, Docker container status, container error logs,
and EAI log monitoring (real-time tail -F with log parsing).

Phase 2: Added get_container_error_logs() for docker logs error extraction
Phase 3: Added EaiLogWatcher for real-time EAI log monitoring (replaces
         the standalone eai_log_monitor SSH-based service on 165)

Changes from acc_agent.py:
  - Removed 'requests' dependency -> uses urllib.request
  - Removed 'dataclasses' dependency -> uses plain classes (Python 3.6 compat)
  - Fixed EAI log file paths: uses backslash in filenames (matches 163 actual files)
  - Fixed server_url to http://172.17.10.165:5004
  - Log output to /opt/acc-monitor-agent/acc_agent.log (same dir as old agent)
"""
import os
import re
import sys
import time
import json
import socket
import logging
import subprocess
import threading
import queue
import urllib.request
import urllib.error
from datetime import datetime
from pathlib import Path
from logging.handlers import RotatingFileHandler

# typing imports (Python 3.6 compatible)
try:
    from typing import Optional, Dict, List, Tuple
except ImportError:
    pass

# ---------------------------------------------------------------------------
# Constants & Configuration
# ---------------------------------------------------------------------------
SCRIPT_DIR = Path(__file__).parent.resolve()
CONFIG_FILE = SCRIPT_DIR / 'agent_config.json'
LOG_FILE = SCRIPT_DIR / 'acc_agent.log'
VERSION = '3.0.0'

CONFIG = {
    'server_url': 'http://172.17.10.165:5004',
    'server_id': '163',
    'report_interval': 30,
    'containers': ['hulu-eai', 'redis'],
    'log_path': '/var/eai/logs',
    'log_level': 'INFO',
    # EAI log monitoring config
    'eai_monitor_enabled': True,
    'eai_log_files': {
        'FLOW_DP-EPS\\IPA MES\u62a5\u5de5\u63a5\u53e3.log': {
            'schema': 'dpeps1',
            'description': 'DP-EPS IPA'
        },
        'FLOW_SMT\\MID-Line2MES\u62a5\u5de5\u63a5\u53e3.log': {
            'schema': 'smt2',
            'description': 'SMT Line2'
        },
        'FLOW_DP-SMT\\MID\\EPP MES\u62a5\u5de5\u63a5\u53e3.log': {
            'schema': 'dpepp1',
            'description': 'DP-SMT MID EPP'
        }
    },
    'eai_report_url': None,
    'eai_batch_size': 10,
    'eai_batch_timeout': 5,
    'eai_catchup_lines': 1000
}

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------

def setup_logging(level_name='INFO'):
    """Configure rotating file + console logging."""
    _logger = logging.getLogger('acc_agent')
    _logger.setLevel(getattr(logging, level_name.upper(), logging.INFO))
    if _logger.handlers:
        return _logger

    fmt = logging.Formatter('%(asctime)s [%(levelname)s] %(message)s',
                            datefmt='%Y-%m-%d %H:%M:%S')

    fh = RotatingFileHandler(str(LOG_FILE), maxBytes=5 * 1024 * 1024,
                             backupCount=3, encoding='utf-8')
    fh.setFormatter(fmt)
    _logger.addHandler(fh)

    ch = logging.StreamHandler(sys.stdout)
    ch.setFormatter(fmt)
    _logger.addHandler(ch)

    return _logger


logger = setup_logging(CONFIG.get('log_level', 'INFO'))


# ---------------------------------------------------------------------------
# HTTP helper (replaces requests library)
# ---------------------------------------------------------------------------

def http_post_json(url, data, timeout=10):
    """POST JSON data using urllib (no external dependencies)."""
    payload = json.dumps(data, ensure_ascii=False).encode('utf-8')
    req = urllib.request.Request(
        url,
        data=payload,
        headers={'Content-Type': 'application/json; charset=utf-8'},
        method='POST'
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            body = resp.read().decode('utf-8')
            return json.loads(body) if body else {}
    except urllib.error.HTTPError as e:
        logger.error("HTTP POST %s -> %s %s", url, e.code, e.reason)
        raise
    except urllib.error.URLError as e:
        logger.error("HTTP POST %s -> URLError: %s", url, e.reason)
        raise
    except Exception as e:
        logger.error("HTTP POST %s -> %s", url, e)
        raise


# =============================================================================
# EAI Log Parser (ported from eai_log_monitor/log_parser.py)
# Preserves 100% functional equivalence with the original parser
# =============================================================================

class TriggerData(object):
    """Trigger data extracted from db trigger get data"""
    def __init__(self, line='', pack_id='', wono='', cnt='', part_no='', raw_data=''):
        self.line = line
        self.pack_id = pack_id
        self.wono = wono
        self.cnt = cnt
        self.part_no = part_no
        self.raw_data = raw_data


class ReportRecord(object):
    """Parsed report record"""
    def __init__(self, schb_number='', source_bill_no='', qty=0.0,
                 product_code='', process_code='', report_time='',
                 worker_code='', lot_number='', line='',
                 raw_request='', raw_response='', is_success=True,
                 error_message='', schema=''):
        self.schb_number = schb_number
        self.source_bill_no = source_bill_no
        self.qty = qty
        self.product_code = product_code
        self.process_code = process_code
        self.report_time = report_time
        self.worker_code = worker_code
        self.lot_number = lot_number
        self.line = line
        self.raw_request = raw_request
        self.raw_response = raw_response
        self.is_success = is_success
        self.error_message = error_message
        self.schema = schema

    def to_dict(self):
        """Convert to dictionary for JSON serialization"""
        return {
            'schb_number': self.schb_number,
            'source_bill_no': self.source_bill_no,
            'qty': self.qty,
            'product_code': self.product_code,
            'process_code': self.process_code,
            'report_time': self.report_time,
            'worker_code': self.worker_code,
            'lot_number': self.lot_number,
            'line': self.line,
            'raw_request': self.raw_request,
            'raw_response': self.raw_response,
            'is_success': self.is_success,
            'error_message': self.error_message,
            'schema': self.schema
        }


class EaiLogParser(object):
    """
    EAI log parser - functionally equivalent to eai_log_monitor/log_parser.py

    Processes trigger -> request -> response flow:
    1. Trigger data (db trigger get data) -> cache LINE info
    2. Kingdee request -> associate with trigger, set as current request
    3. Kingdee response -> pair with current request, return record
    """

    LOG_LINE_PATTERN = re.compile(
        r'\[(\w+)\]\[(\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2})\.\d+\]\[.*?\]\[.*?\]\s*(.*)',
        re.DOTALL
    )

    TRIGGER_DATA_PATTERN = re.compile(
        r'db\s+trigger\s+get\s+data:\s*(\[.*\])',
        re.IGNORECASE | re.DOTALL
    )

    KINGDEE_REQUEST_PATTERN = re.compile(
        r'kingdee\s+request\s+json\s*:\s*(\{.*)',
        re.IGNORECASE | re.DOTALL
    )

    KINGDEE_RESPONSE_PATTERN = re.compile(
        r'kingdee\s+response\s+json\s*:\s*(\{.*)',
        re.IGNORECASE | re.DOTALL
    )

    SUCCESS_PATTERN = re.compile(r'"IsSuccess"\s*:\s*true', re.IGNORECASE)
    FAILURE_PATTERN = re.compile(r'"IsSuccess"\s*:\s*false', re.IGNORECASE)

    LUA_ERROR_PATTERN = re.compile(
        r'run\s+error:\s+call\s+lua\s+error:.*?(\{.*)',
        re.IGNORECASE | re.DOTALL
    )

    ERROR_MESSAGE_PATTERN = re.compile(r'"Message"\s*:\s*"([^"]+)"', re.IGNORECASE)

    FIELD_PATTERNS = {
        'FMoBillNo': re.compile(r'FMoBillNo[\\\"]*:[\\\"]*([A-Z]{2,4}-?\d{8,9})'),
        'FSrcBillNo': re.compile(r'FSrcBillNo[\\\"]*:[\\\"]*([A-Z]{2,4}-?\d{8,9})'),
        'FFinishQty': re.compile(r'FFinishQty[\\\"]*:(\d+(?:\.\d+)?)'),
        'FQuaQty': re.compile(r'FQuaQty[\\\"]*:(\d+(?:\.\d+)?)'),
        'FMaterialId_FNumber': re.compile(r'FMaterialId[\\\"]*:\{[\\\"]*FNumber[\\\"]*:[\\\"]*([A-Z0-9.\-]+)'),
        'FLot_FNumber': re.compile(r'FLot[\\\"]*:\{[\\\"]*FNumber[\\\"]*:[\\\"]*(\d{8}[A-Z]\d{7})'),
        'FDate': re.compile(r'FDate[\\\"]*:[\\\"]*(\d{4}-\d{2}-\d{2})'),
    }

    def __init__(self):
        self._trigger_queues = {}  # type: Dict[str, list]
        self._current_request = None  # type: Optional[Tuple]

    def parse_line(self, line):
        """Parse a single log line, return ReportRecord if a complete record is found"""
        try:
            line = line.strip()
            if not line:
                return None

            timestamp = None
            match = self.LOG_LINE_PATTERN.match(line)
            if match:
                level, time_str, content = match.groups()
                try:
                    timestamp = datetime.strptime(time_str, '%Y-%m-%d %H:%M:%S')
                except ValueError:
                    timestamp = datetime.now()
            else:
                content = line
                timestamp = datetime.now()

            # Step 1: Check for Lua error (highest priority)
            lua_error_match = self.LUA_ERROR_PATTERN.search(line)
            if lua_error_match:
                return self._handle_lua_error(timestamp, lua_error_match.group(1), line)

            # Step 2: Check for trigger data
            trigger_match = self.TRIGGER_DATA_PATTERN.search(line)
            if trigger_match:
                self._handle_trigger_data(trigger_match.group(1))
                return None

            # Step 3: Check for kingdee request
            req_match = self.KINGDEE_REQUEST_PATTERN.search(content)
            if req_match:
                self._handle_request(timestamp, req_match.group(1))
                return None

            # Step 4: Check for kingdee response
            resp_match = self.KINGDEE_RESPONSE_PATTERN.search(content)
            if resp_match:
                return self._handle_response(timestamp, resp_match.group(1))

            return None
        except Exception as e:
            logger.warning("Parse line error: %s, content: %s...", e, line[:100])
            return None

    def _handle_trigger_data(self, json_str):
        """Process trigger data (db trigger get data)"""
        try:
            data_list = json.loads(json_str)
            if not data_list or not isinstance(data_list, list):
                return

            data = data_list[0]
            trigger = TriggerData(
                line=data.get('LINE', ''),
                pack_id=data.get('PACKID', ''),
                wono=data.get('WONO', ''),
                cnt=data.get('CNT', ''),
                part_no=data.get('PARTNO', ''),
                raw_data=json_str
            )

            wono = trigger.wono
            if not wono:
                return
            if wono not in self._trigger_queues:
                self._trigger_queues[wono] = []
            self._trigger_queues[wono].append(trigger)
            logger.debug("Enqueue trigger: LINE=%s, WONO=%s, queue depth=%d",
                         trigger.line, wono, len(self._trigger_queues[wono]))

        except (json.JSONDecodeError, ValueError) as e:
            logger.warning("Trigger JSON parse error: %s", e)
        except Exception as e:
            logger.warning("Trigger data error: %s", e)

    def _handle_request(self, timestamp, json_str):
        """Process kingdee request"""
        data = None
        source_bill_no = None

        try:
            data = json.loads(json_str)
            if 'data' in data and isinstance(data['data'], str):
                try:
                    inner_data = json.loads(data['data'])
                    data['_parsed_data'] = inner_data
                except (json.JSONDecodeError, ValueError):
                    pass
            source_bill_no = self._extract_source_bill_no(data)

        except (json.JSONDecodeError, ValueError):
            data, source_bill_no = self._extract_from_truncated_json(json_str)
            if not data:
                fallback_trigger = self._pop_oldest_trigger_any()
                if fallback_trigger:
                    data = {
                        '_from_trigger': True,
                        '_raw_request': json_str,
                        '_parsed_data': {
                            'FMoBillNo': fallback_trigger.wono,
                            'FFinishQty': float(fallback_trigger.cnt) if fallback_trigger.cnt else 0,
                            'FQuaQty': float(fallback_trigger.cnt) if fallback_trigger.cnt else 0,
                            'FMaterialId': {'FNumber': fallback_trigger.part_no},
                            'FLot': {'FNumber': fallback_trigger.pack_id},
                        }
                    }
                    source_bill_no = fallback_trigger.wono
                    line_name = fallback_trigger.line
                    self._current_request = (timestamp, data, source_bill_no, line_name)
                    return
                else:
                    return
        except Exception:
            return

        line_name = ''
        matched_trigger = self._pop_trigger_for_wono(source_bill_no) if source_bill_no else None
        if matched_trigger:
            line_name = matched_trigger.line
        elif self._trigger_queues:
            fallback = self._pop_oldest_trigger_any()
            if fallback:
                line_name = fallback.line
                if not source_bill_no:
                    source_bill_no = fallback.wono

        self._current_request = (timestamp, data, source_bill_no, line_name)

    def _handle_response(self, timestamp, json_str):
        """Process kingdee response, pair with current request"""
        try:
            use_trigger_fallback = False
            if not self._current_request:
                fallback_trigger = self._pop_oldest_trigger_any()
                if fallback_trigger:
                    use_trigger_fallback = True
                    req_data = {
                        '_from_trigger': True,
                        'WONO': fallback_trigger.wono,
                        'LINE': fallback_trigger.line,
                        'PACKID': fallback_trigger.pack_id,
                        'CNT': fallback_trigger.cnt,
                        'PARTNO': fallback_trigger.part_no,
                        '_parsed_data': {
                            'FMoBillNo': fallback_trigger.wono,
                            'FFinishQty': float(fallback_trigger.cnt) if fallback_trigger.cnt else 0,
                            'FQuaQty': float(fallback_trigger.cnt) if fallback_trigger.cnt else 0,
                            'FMaterialId': {'FNumber': fallback_trigger.part_no},
                            'FLot': {'FNumber': fallback_trigger.pack_id},
                        }
                    }
                    source_bill_no = fallback_trigger.wono
                    line_name = fallback_trigger.line
                else:
                    return None
            else:
                req_timestamp, req_data, source_bill_no, line_name = self._current_request
                if not line_name:
                    late_trigger = self._pop_trigger_for_wono(source_bill_no) if source_bill_no else None
                    if late_trigger:
                        line_name = late_trigger.line

            self._current_request = None

            is_success = self.SUCCESS_PATTERN.search(json_str) is not None
            is_failure = self.FAILURE_PATTERN.search(json_str) is not None

            if is_success:
                try:
                    resp_data = json.loads(json_str)
                    schb_number = self._extract_schb_number_from_response(resp_data)
                    if not schb_number:
                        return None
                    return self._build_record(req_data, resp_data, json_str, schb_number, source_bill_no, line_name)
                except (json.JSONDecodeError, ValueError):
                    schb_number = self._extract_schb_from_truncated(json_str)
                    if schb_number:
                        return self._build_record(req_data, {}, json_str, schb_number, source_bill_no, line_name)
                    return None

            elif is_failure:
                error_message = self._extract_error_message(json_str)
                return self._build_failure_record(
                    req_data=req_data,
                    raw_response=json_str,
                    source_bill_no=source_bill_no,
                    line_name=line_name,
                    error_message=error_message
                )
            else:
                return None

        except Exception as e:
            logger.warning("Response handling error: %s", e)
            return None

    def _handle_lua_error(self, timestamp, json_str, raw_line):
        """Process Lua execution error"""
        try:
            error_message = ''
            source_bill_no = ''
            line_name = ''

            try:
                data = json.loads(json_str)
                if 'errorMsg' in data:
                    error_msg = data['errorMsg']
                    if 'ERP\u62a5\u5de5\u8fd4\u56de\u5931\u8d25' in error_msg:
                        nested_json_match = re.search(r'\{.*"Errors".*\}', error_msg)
                        if nested_json_match:
                            nested_error = self._extract_error_message(nested_json_match.group(0))
                            if nested_error and nested_error != '\u6267\u884c\u9519\u8bef':
                                error_message = nested_error
                            else:
                                error_message = error_msg.split('ERP\u62a5\u5de5\u8fd4\u56de\u5931\u8d25')[1] if 'ERP\u62a5\u5de5\u8fd4\u56de\u5931\u8d25' in error_msg else error_msg
                        else:
                            error_message = error_msg
                    else:
                        error_message = error_msg

                if 'data' in data:
                    try:
                        inner_data = json.loads(data['data']) if isinstance(data['data'], str) else data['data']
                        line_name = inner_data.get('LINE', '')
                        source_bill_no = inner_data.get('WONO', '')
                    except Exception:
                        pass

            except (json.JSONDecodeError, ValueError):
                error_msg_match = re.search(r'"errorMsg"\s*:\s*"([^"]*(?:\\.[^"]*)*)"', json_str)
                if error_msg_match:
                    error_message = error_msg_match.group(1).replace('\\n', ' ').replace('\\r', ' ')

                line_match = re.search(r'"LINE"\s*:\s*"([^"]+)"', json_str)
                if line_match:
                    line_name = line_match.group(1)

                wono_match = re.search(r'"WONO"\s*:\s*"([^"]+)"', json_str)
                if wono_match:
                    source_bill_no = wono_match.group(1)

            if not line_name:
                lua_trigger = (self._pop_trigger_for_wono(source_bill_no) if source_bill_no
                               else self._pop_oldest_trigger_any())
                if lua_trigger:
                    line_name = lua_trigger.line
                    if not source_bill_no:
                        source_bill_no = lua_trigger.wono

            if error_message:
                error_message = error_message.replace('\\r\\n', ' ').replace('\\n', ' ').replace('\\r', ' ')
                error_message = re.sub(r'\s+', ' ', error_message).strip()
                if len(error_message) > 500:
                    error_message = error_message[:500] + '...'
            else:
                error_message = 'Lua\u6267\u884c\u9519\u8bef'

            if self._current_request and self._current_request[2] == source_bill_no:
                self._current_request = None

            fail_id = "FAIL_%s" % datetime.now().strftime('%Y%m%d%H%M%S%f')

            return ReportRecord(
                schb_number=fail_id,
                source_bill_no=source_bill_no or 'UNKNOWN',
                qty=0,
                product_code='',
                process_code='',
                report_time=timestamp.isoformat(),
                worker_code='',
                lot_number='',
                line=line_name,
                raw_request='',
                raw_response=raw_line[:2000],
                is_success=False,
                error_message=error_message
            )
        except Exception as e:
            logger.warning("Lua error handling failed: %s", e)
            return None

    # --- Helper methods ---

    def _pop_trigger_for_wono(self, wono):
        q = self._trigger_queues.get(wono)
        if q:
            trigger = q.pop(0)
            if not q:
                del self._trigger_queues[wono]
            return trigger
        return None

    def _pop_oldest_trigger_any(self):
        for wono, q in list(self._trigger_queues.items()):
            if q:
                trigger = q.pop(0)
                if not q:
                    del self._trigger_queues[wono]
                return trigger
        return None

    def _extract_source_bill_no(self, data):
        possible_keys = ['FMoBillNo', 'FSrcBillNo', 'FBillNo', 'SCHB_NUMBER', 'schb_number', 'BillNo']
        search_data = data.get('_parsed_data', data)
        for key in possible_keys:
            if key in search_data and search_data[key]:
                return str(search_data[key])
        if 'Model' in search_data:
            for key in possible_keys:
                if key in search_data['Model'] and search_data['Model'][key]:
                    return str(search_data['Model'][key])
        if 'FEntity' in search_data and isinstance(search_data['FEntity'], list) and search_data['FEntity']:
            for key in possible_keys:
                if key in search_data['FEntity'][0] and search_data['FEntity'][0][key]:
                    return str(search_data['FEntity'][0][key])
        return self._recursive_search(search_data, possible_keys)

    def _recursive_search(self, data, keys, depth=3):
        if depth <= 0:
            return None
        if isinstance(data, dict):
            for key in keys:
                if key in data:
                    return str(data[key])
            for v in data.values():
                result = self._recursive_search(v, keys, depth - 1)
                if result:
                    return result
        elif isinstance(data, list):
            for item in data:
                result = self._recursive_search(item, keys, depth - 1)
                if result:
                    return result
        return None

    def _extract_from_truncated_json(self, json_str):
        extracted = {'_truncated': True, '_raw_request': json_str}
        source_bill_no = None
        for key in ['FMoBillNo', 'FSrcBillNo']:
            if key in self.FIELD_PATTERNS:
                match = self.FIELD_PATTERNS[key].search(json_str)
                if match:
                    source_bill_no = match.group(1)
                    extracted[key] = source_bill_no
                    break
        if not source_bill_no:
            return None, None
        for field_name, pattern in self.FIELD_PATTERNS.items():
            if field_name not in extracted:
                match = pattern.search(json_str)
                if match:
                    value = match.group(1)
                    if field_name in ['FFinishQty', 'FQuaQty']:
                        try:
                            value = float(value)
                        except ValueError:
                            pass
                    extracted[field_name] = value
        extracted['_parsed_data'] = {
            'FMoBillNo': source_bill_no,
            'FFinishQty': extracted.get('FFinishQty', 0),
            'FQuaQty': extracted.get('FQuaQty', 0),
            'FMaterialId': {'FNumber': extracted.get('FMaterialId_FNumber', '')},
            'FLot': {'FNumber': extracted.get('FLot_FNumber', '')},
        }
        return extracted, source_bill_no

    def _extract_schb_number_from_response(self, data):
        possible_keys = ['FBillNo', 'Number', 'BillNo', 'SCHB_NUMBER']
        if 'Result' in data and isinstance(data['Result'], dict):
            result = data['Result']
            if 'ResponseStatus' in result and isinstance(result['ResponseStatus'], dict):
                for key in possible_keys:
                    if key in result['ResponseStatus']:
                        return str(result['ResponseStatus'][key])
            for key in possible_keys:
                if key in result:
                    return str(result[key])
        return self._recursive_search(data, possible_keys)

    def _extract_schb_from_truncated(self, json_str):
        patterns = [
            re.compile(r'"Number"\s*:\s*"([^"]+)"', re.IGNORECASE),
            re.compile(r'"FBillNo"\s*:\s*"([^"]+)"', re.IGNORECASE),
            re.compile(r'"BillNo"\s*:\s*"([^"]+)"', re.IGNORECASE),
            re.compile(r'"SCHB_NUMBER"\s*:\s*"([^"]+)"', re.IGNORECASE),
        ]
        for pat in patterns:
            m = pat.search(json_str)
            if m:
                return m.group(1)
        return None

    def _extract_field(self, data, keys, default=None):
        search_data = data.get('_parsed_data', data)
        for key in keys:
            if key in search_data:
                value = search_data[key]
                if isinstance(value, dict) and 'FNumber' in value:
                    return value['FNumber']
                return value
        if 'Model' in search_data and isinstance(search_data['Model'], dict):
            for key in keys:
                if key in search_data['Model']:
                    value = search_data['Model'][key]
                    if isinstance(value, dict) and 'FNumber' in value:
                        return value['FNumber']
                    return value
        if 'FEntity' in search_data and isinstance(search_data['FEntity'], list) and search_data['FEntity']:
            for key in keys:
                if key in search_data['FEntity'][0]:
                    value = search_data['FEntity'][0][key]
                    if isinstance(value, dict) and 'FNumber' in value:
                        return value['FNumber']
                    return value
        return default

    def _extract_error_message(self, json_str):
        try:
            data = json.loads(json_str)
            if 'Result' in data and isinstance(data['Result'], dict):
                result = data['Result']
                if 'ResponseStatus' in result and isinstance(result['ResponseStatus'], dict):
                    resp_status = result['ResponseStatus']
                    if 'Errors' in resp_status and isinstance(resp_status['Errors'], list):
                        errors = resp_status['Errors']
                        if errors:
                            messages = []
                            for err in errors:
                                if isinstance(err, dict) and 'Message' in err:
                                    msg = err['Message'].replace('\\r\\n', ' ').replace('\\n', ' ').replace('\\r', ' ').strip()
                                    if msg:
                                        messages.append(msg)
                            if messages:
                                return '; '.join(messages)
        except (json.JSONDecodeError, ValueError):
            pass
        matches = self.ERROR_MESSAGE_PATTERN.findall(json_str)
        if matches:
            return matches[0].replace('\\r\\n', ' ').replace('\\n', ' ').replace('\\r', ' ').strip()
        return '\u6267\u884c\u9519\u8bef'

    def _build_record(self, req_data, resp_data, raw_response, schb_number, source_bill_no, line_name=''):
        try:
            if not schb_number:
                return None
            qty = self._extract_field(req_data, ['FFinishQty', 'FQuaQty', 'FQty', 'Qty', 'qty', 'FMustQty'], default=0)
            product_code = self._extract_field(req_data, ['FMaterialId', 'FMaterialNumber', 'ProductCode'], default='')
            process_code = self._extract_field(req_data, ['FOperNumber', 'ProcessCode'], default='')
            worker_code = self._extract_field(req_data, ['FWorkerId', 'WorkerCode', 'FWorkerNumber'], default='')
            lot_number = self._extract_field(req_data, ['FLot'], default='')

            if req_data.get('_from_trigger'):
                if not qty:
                    qty = float(req_data.get('CNT', 0) or 0)
                if not product_code:
                    product_code = req_data.get('PARTNO', '')
                if not lot_number:
                    lot_number = req_data.get('PACKID', '')

            if isinstance(qty, str):
                try:
                    qty = float(qty)
                except ValueError:
                    qty = 0

            if req_data.get('_truncated'):
                raw_request = req_data.get('_raw_request', '')
            else:
                raw_request = json.dumps(req_data, ensure_ascii=False)

            return ReportRecord(
                schb_number=schb_number,
                source_bill_no=source_bill_no or '',
                qty=float(qty) if qty else 0,
                product_code=str(product_code) if product_code else '',
                process_code=str(process_code) if process_code else '',
                report_time=datetime.now().isoformat(),
                worker_code=str(worker_code) if worker_code else '',
                lot_number=str(lot_number) if lot_number else '',
                line=line_name or '',
                raw_request=raw_request,
                raw_response=raw_response,
                is_success=True
            )
        except Exception as e:
            logger.warning("Build record error: %s", e)
            return None

    def _build_failure_record(self, req_data, raw_response, source_bill_no, line_name, error_message):
        if req_data.get('_truncated'):
            raw_request = req_data.get('_raw_request', '')
        else:
            raw_request = json.dumps(req_data, ensure_ascii=False)

        qty = self._extract_field(req_data, ['FFinishQty', 'FQuaQty', 'FQty', 'Qty'], default=0)
        product_code = self._extract_field(req_data, ['FMaterialId', 'FMaterialNumber', 'ProductCode'], default='')
        lot_number = self._extract_field(req_data, ['FLot'], default='')

        if req_data.get('_from_trigger'):
            if not qty:
                qty = float(req_data.get('CNT', 0) or 0)
            if not product_code:
                product_code = req_data.get('PARTNO', '')
            if not lot_number:
                lot_number = req_data.get('PACKID', '')

        if isinstance(qty, str):
            try:
                qty = float(qty)
            except ValueError:
                qty = 0

        fail_id = "FAIL_%s" % datetime.now().strftime('%Y%m%d%H%M%S%f')

        return ReportRecord(
            schb_number=fail_id,
            source_bill_no=source_bill_no or 'UNKNOWN',
            qty=float(qty) if qty else 0,
            product_code=str(product_code) if product_code else '',
            process_code='',
            report_time=datetime.now().isoformat(),
            worker_code='',
            lot_number=str(lot_number) if lot_number else '',
            line=line_name or '',
            raw_request=raw_request,
            raw_response=raw_response[:4000],
            is_success=False,
            error_message=error_message
        )


# =============================================================================
# EAI Log File Watcher (replaces SSH-based SSHLogMonitor)
# Reads local files directly using tail -F subprocess
# =============================================================================

class EaiLogWatcher(object):
    """
    Watches a single EAI log file using tail -F subprocess.
    Runs locally on the 163 server -- no SSH needed.
    """

    def __init__(self, log_file, schema, description, log_dir, catchup_lines=1000):
        self.log_file = log_file
        self.schema = schema
        self.description = description
        self.full_path = os.path.join(log_dir, log_file)
        self.catchup_lines = catchup_lines

        self._parser = EaiLogParser()
        self._record_queue = queue.Queue()
        self._running = False
        self._thread = None
        self._process = None

    def start(self):
        """Start watching the log file"""
        self._running = True
        self._thread = threading.Thread(target=self._watch_loop)
        self._thread.daemon = True
        self._thread.start()
        logger.info("[EAI] Started watcher: %s (%s) -> %s", self.description, self.log_file, self.full_path)

    def stop(self):
        """Stop watching"""
        self._running = False
        if self._process:
            try:
                self._process.terminate()
                self._process.wait(timeout=5)
            except Exception:
                try:
                    self._process.kill()
                except Exception:
                    pass
        if self._thread:
            self._thread.join(timeout=5)
        logger.info("[EAI] Stopped watcher: %s", self.description)

    def get_records(self):
        """Get parsed records (non-blocking)"""
        records = []
        while True:
            try:
                record = self._record_queue.get_nowait()
                records.append(record)
            except queue.Empty:
                break
        return records

    def _watch_loop(self):
        """Main watch loop with auto-reconnect on file rotation"""
        while self._running:
            try:
                if not os.path.exists(self.full_path):
                    logger.warning("[EAI] Log file not found: %s, retrying in 10s...", self.full_path)
                    time.sleep(10)
                    continue

                # Phase 1: Catch-up - read recent lines to avoid missing data
                self._catchup()

                # Phase 2: Real-time tail -F
                self._tail_follow()

            except Exception as e:
                logger.error("[EAI] Watcher error for %s: %s", self.description, e)

            if self._running:
                logger.warning("[EAI] %s tail process ended, reconnecting in 5s...", self.description)
                time.sleep(5)

    def _catchup(self):
        """Read recent lines for catch-up after restart"""
        try:
            cmd = 'tail -n %d "%s"' % (self.catchup_lines, self.full_path)
            result = subprocess.run(
                cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                timeout=30
            )
            stdout_text = result.stdout.decode('utf-8', errors='replace')
            if stdout_text:
                count = 0
                for line in stdout_text.splitlines():
                    record = self._parser.parse_line(line)
                    if record:
                        record.schema = self.schema
                        self._record_queue.put(record)
                        count += 1
                logger.info("[EAI] Catchup complete for %s: %d records from %d lines",
                            self.description, count, self.catchup_lines)
        except Exception as e:
            logger.warning("[EAI] Catchup error for %s: %s", self.description, e)

    def _tail_follow(self):
        """Follow log file using tail -F (handles file rotation)"""
        cmd = ['tail', '-F', self.full_path]
        try:
            self._process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                bufsize=1
            )

            logger.info("[EAI] tail -F started for %s (pid=%d)", self.description, self._process.pid)

            for raw_line in iter(self._process.stdout.readline, b''):
                if not self._running:
                    break
                try:
                    line = raw_line.decode('utf-8', errors='replace').rstrip('\n')
                except Exception:
                    continue
                if line:
                    record = self._parser.parse_line(line)
                    if record:
                        record.schema = self.schema
                        self._record_queue.put(record)

        except Exception as e:
            logger.error("[EAI] tail -F error for %s: %s", self.description, e)
        finally:
            if self._process:
                try:
                    self._process.terminate()
                    self._process.wait(timeout=3)
                except Exception:
                    try:
                        self._process.kill()
                    except Exception:
                        pass
                self._process = None


# =============================================================================
# EAI Log Monitor Manager
# =============================================================================

class EaiLogMonitorManager(object):
    """
    Manages multiple EaiLogWatcher instances and batches records
    for HTTP upload to the monitoring center.
    """

    def __init__(self, config, report_url):
        self.config = config
        self.report_url = report_url
        self._watchers = {}
        self._running = False
        self._batch_thread = None
        self._stats = {
            'total_records': 0,
            'uploaded_records': 0,
            'failed_uploads': 0
        }

    def start(self):
        """Start all watchers and the batch upload thread"""
        self._running = True
        log_dir = self.config.get('log_path', '/var/eai/logs')
        eai_log_files = self.config.get('eai_log_files', {})
        catchup_lines = self.config.get('eai_catchup_lines', 1000)

        for log_file, file_config in eai_log_files.items():
            watcher = EaiLogWatcher(
                log_file=log_file,
                schema=file_config['schema'],
                description=file_config['description'],
                log_dir=log_dir,
                catchup_lines=catchup_lines
            )
            self._watchers[log_file] = watcher
            watcher.start()

        # Start batch upload thread
        self._batch_thread = threading.Thread(target=self._batch_upload_loop)
        self._batch_thread.daemon = True
        self._batch_thread.start()
        logger.info("[EAI] Monitor manager started with %d watchers", len(self._watchers))

    def stop(self):
        """Stop all watchers and the batch thread"""
        self._running = False
        for watcher in self._watchers.values():
            watcher.stop()
        if self._batch_thread:
            self._batch_thread.join(timeout=10)
        logger.info("[EAI] Monitor manager stopped. Stats: %s", self._stats)

    def get_stats(self):
        """Get monitoring statistics"""
        return dict(self._stats)

    def _batch_upload_loop(self):
        """Collect records from all watchers and upload in batches"""
        batch_size = self.config.get('eai_batch_size', 10)
        batch_timeout = self.config.get('eai_batch_timeout', 5)
        batch_records = {}
        last_upload_time = time.time()

        while self._running:
            try:
                # Collect records from all watchers
                for log_file, watcher in self._watchers.items():
                    records = watcher.get_records()
                    for record in records:
                        schema = record.schema
                        if schema not in batch_records:
                            batch_records[schema] = []
                        batch_records[schema].append(record.to_dict())
                        self._stats['total_records'] += 1

                # Check if we should upload
                current_time = time.time()
                should_upload = False

                for records in batch_records.values():
                    if len(records) >= batch_size:
                        should_upload = True
                        break

                if current_time - last_upload_time >= batch_timeout:
                    should_upload = True

                if should_upload and any(batch_records.values()):
                    self._upload_records(batch_records)
                    last_upload_time = current_time

                time.sleep(0.5)

            except Exception as e:
                logger.error("[EAI] Batch upload loop error: %s", e)
                time.sleep(1)

    def _upload_records(self, batch_records):
        """Upload batched records to the monitoring center"""
        for schema, records in list(batch_records.items()):
            if not records:
                continue
            try:
                payload = {
                    'server_id': self.config.get('server_id', '163'),
                    'schema': schema,
                    'records': records,
                    'timestamp': datetime.utcnow().isoformat()
                }

                resp_data = http_post_json(self.report_url, payload, timeout=15)

                inserted = resp_data.get('data', {}).get('inserted', 0) if resp_data else 0
                self._stats['uploaded_records'] += inserted

                logger.info("[EAI] Uploaded %d records to schema %s, inserted: %d",
                            len(records), schema, inserted)
                batch_records[schema] = []  # Clear only on success

            except Exception as e:
                self._stats['failed_uploads'] += 1
                logger.error("[EAI] Upload failed for schema %s: %s", schema, e)
                # Keep records in buffer for retry next cycle


# =============================================================================
# Main Agent Class
# =============================================================================

class AccLinuxAgent(object):
    """Linux monitoring agent for Docker containers and EAI log monitoring"""

    def __init__(self, config):
        self.config = config
        self.server_url = config['server_url']
        self.server_id = config['server_id']
        self._eai_manager = None

    def run_command(self, cmd):
        """Run shell command and return output"""
        try:
            result = subprocess.run(
                cmd,
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=30
            )
            return result.stdout.decode('utf-8', errors='replace').strip()
        except Exception as e:
            logger.error("Error running command '%s': %s", cmd, e)
            return ""

    def get_cpu_usage(self):
        """Get CPU usage from /proc/stat (no external tools)"""
        try:
            with open('/proc/stat', 'r') as f:
                line = f.readline()
            parts = line.split()
            # user, nice, system, idle, iowait, irq, softirq, steal
            idle = int(parts[4])
            total = sum(int(x) for x in parts[1:])
            # Need two samples
            time.sleep(0.1)
            with open('/proc/stat', 'r') as f:
                line2 = f.readline()
            parts2 = line2.split()
            idle2 = int(parts2[4])
            total2 = sum(int(x) for x in parts2[1:])
            diff_idle = idle2 - idle
            diff_total = total2 - total
            if diff_total == 0:
                return 0.0
            return round((1.0 - float(diff_idle) / float(diff_total)) * 100.0, 1)
        except Exception:
            return 0.0

    def get_memory_usage(self):
        """Get memory usage from /proc/meminfo (no external tools)"""
        try:
            info = {}
            with open('/proc/meminfo', 'r') as f:
                for line in f:
                    parts = line.split()
                    if len(parts) >= 2:
                        key = parts[0].rstrip(':')
                        info[key] = int(parts[1])
            total = info.get('MemTotal', 1)
            available = info.get('MemAvailable', info.get('MemFree', 0))
            used_pct = round((1.0 - float(available) / float(total)) * 100.0, 1)
            return used_pct
        except Exception:
            return 0.0

    def get_disk_usage(self, path='/'):
        """Get disk usage percentage"""
        try:
            output = self.run_command(
                "df %s | tail -1 | awk '{print $5}' | tr -d '%%'" % path
            )
            return float(output) if output else 0
        except Exception:
            return 0

    def get_container_status(self):
        """Get Docker container status"""
        containers = []
        monitored = self.config.get('containers', [])

        for container_name in monitored:
            container_info = {
                'name': container_name,
                'status': 'unknown',
                'container_id': '',
                'cpu_percent': 0,
                'memory_usage': 0,
                'memory_limit': 0,
                'restart_count': 0
            }

            try:
                inspect_cmd = "docker inspect %s 2>/dev/null" % container_name
                output = self.run_command(inspect_cmd)

                if output:
                    data = json.loads(output)
                    if data:
                        container = data[0]
                        state = container.get('State', {})

                        container_info['container_id'] = container.get('Id', '')[:12]
                        container_info['status'] = 'running' if state.get('Running') else 'stopped'
                        container_info['restart_count'] = container.get('RestartCount', 0)

                        stats_cmd = ("timeout 5 docker stats %s --no-stream "
                                     "--format '{{.CPUPerc}}|{{.MemUsage}}'") % container_name
                        stats = self.run_command(stats_cmd)

                        if stats:
                            parts = stats.split('|')
                            if len(parts) >= 2:
                                cpu = parts[0].replace('%', '')
                                container_info['cpu_percent'] = float(cpu) if cpu else 0

                                mem_parts = parts[1].split('/')
                                if len(mem_parts) >= 2:
                                    container_info['memory_usage'] = self._parse_memory(mem_parts[0])
                                    container_info['memory_limit'] = self._parse_memory(mem_parts[1])
                else:
                    container_info['status'] = 'not_found'

            except Exception as e:
                logger.error("Error getting container %s status: %s", container_name, e)

            containers.append(container_info)

        return containers

    def _parse_memory(self, mem_str):
        """Parse memory string to MB"""
        mem_str = mem_str.strip().upper()
        try:
            if 'GIB' in mem_str or 'GB' in mem_str:
                return float(mem_str.replace('GIB', '').replace('GB', '').strip()) * 1024
            elif 'MIB' in mem_str or 'MB' in mem_str:
                return float(mem_str.replace('MIB', '').replace('MB', '').strip())
            elif 'KIB' in mem_str or 'KB' in mem_str:
                return float(mem_str.replace('KIB', '').replace('KB', '').strip()) / 1024
            else:
                return float(mem_str)
        except Exception:
            return 0

    def get_container_error_logs(self, minutes=5):
        """
        Get recent error logs from Docker containers.
        Phase 2: Uses 'timeout 10' to prevent docker logs from hanging.
        """
        container_logs = {}
        for container_name in self.config.get('containers', []):
            try:
                cmd = (
                    'timeout 10 docker logs %s '
                    '--since %dm 2>&1 | '
                    'grep -iE "error|exception|failed" | tail -20'
                ) % (container_name, minutes)
                output = self.run_command(cmd)
                if output:
                    errors = []
                    for line in output.split('\n'):
                        line = line.strip()
                        if line and len(line) > 10:
                            errors.append({
                                'message': line[:300],
                                'timestamp': datetime.now().isoformat()
                            })
                    if errors:
                        container_logs[container_name] = errors
            except Exception as e:
                logger.error("Error getting logs for %s: %s", container_name, e)
        return container_logs

    def collect_metrics(self):
        """Collect all metrics including container error logs"""
        metrics = {
            'server_id': self.server_id,
            'hostname': socket.gethostname(),
            'timestamp': datetime.utcnow().isoformat(),
            'resources': {
                'cpu_usage': self.get_cpu_usage(),
                'memory_usage': self.get_memory_usage(),
                'disk_usage': self.get_disk_usage()
            },
            'containers': self.get_container_status(),
            'container_error_logs': self.get_container_error_logs()
        }

        # Include EAI monitor stats if running
        if self._eai_manager:
            metrics['eai_monitor_stats'] = self._eai_manager.get_stats()

        return metrics

    def report_metrics(self, metrics):
        """Send metrics to monitoring center"""
        try:
            url = "%s/api/agent/report" % self.server_url
            http_post_json(url, metrics, timeout=10)
            logger.debug("Metrics reported successfully")
            return True
        except Exception as e:
            logger.error("Error reporting metrics: %s", e)
            return False

    def _start_eai_monitor(self):
        """Start EAI log monitoring if enabled in config"""
        if not self.config.get('eai_monitor_enabled', False):
            logger.info("[EAI] EAI log monitoring is disabled in config")
            return

        eai_log_files = self.config.get('eai_log_files', {})
        if not eai_log_files:
            logger.warning("[EAI] No EAI log files configured")
            return

        # Determine report URL
        report_url = self.config.get('eai_report_url')
        if not report_url:
            report_url = "%s/api/agent/eai-logs" % self.server_url

        self._eai_manager = EaiLogMonitorManager(self.config, report_url)
        self._eai_manager.start()
        logger.info("[EAI] EAI log monitoring started, reporting to %s", report_url)

    def _stop_eai_monitor(self):
        """Stop EAI log monitoring"""
        if self._eai_manager:
            self._eai_manager.stop()
            self._eai_manager = None

    def run(self):
        """Main agent loop"""
        logger.info("ACC Linux Agent v%s started for server %s", VERSION, self.server_id)
        logger.info("Reporting to %s", self.server_url)

        # Start EAI log monitoring (Phase 3)
        self._start_eai_monitor()

        try:
            while True:
                try:
                    metrics = self.collect_metrics()
                    self.report_metrics(metrics)

                    # Log summary
                    containers = metrics.get('containers', [])
                    running = sum(1 for c in containers if c['status'] == 'running')
                    stopped = len(containers) - running

                    eai_stats = ''
                    if self._eai_manager:
                        stats = self._eai_manager.get_stats()
                        eai_stats = " | EAI: %d total, %d uploaded" % (
                            stats.get('total_records', 0),
                            stats.get('uploaded_records', 0)
                        )

                    logger.info(
                        "[OK] CPU:%.1f%% MEM:%.1f%% DISK:%.1f%% | Containers: %d up / %d down%s",
                        metrics['resources']['cpu_usage'],
                        metrics['resources']['memory_usage'],
                        metrics['resources']['disk_usage'],
                        running, stopped, eai_stats
                    )

                except Exception as e:
                    logger.error("Error in main loop: %s", e)

                time.sleep(self.config['report_interval'])
        finally:
            self._stop_eai_monitor()


def load_config():
    """Load configuration from agent_config.json if exists, merge with defaults"""
    config = CONFIG.copy()
    if CONFIG_FILE.exists():
        try:
            with open(str(CONFIG_FILE), 'r', encoding='utf-8') as f:
                user_config = json.load(f)
            config.update(user_config)
            logger.info("Loaded config from %s", CONFIG_FILE)
        except Exception as e:
            logger.warning("Failed to load %s: %s, using defaults", CONFIG_FILE, e)
    else:
        logger.info("No config file found at %s, using defaults", CONFIG_FILE)
    return config


if __name__ == '__main__':
    config = load_config()
    # Re-setup logging with config level
    logger = setup_logging(config.get('log_level', 'INFO'))

    agent = AccLinuxAgent(config)

    try:
        agent.run()
    except KeyboardInterrupt:
        logger.info("Agent stopped by user")
    except Exception as e:
        logger.error("Agent error: %s", e)
        sys.exit(1)

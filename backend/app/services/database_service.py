# -*- coding: utf-8 -*-
"""
ACC Monitor - Database Monitoring Service
"""
import os
from datetime import datetime
from typing import Dict, List, Optional
from config.settings import ORACLE_CONFIGS, Config

# Try to import cx_Oracle, handle if not available
try:
    import cx_Oracle
    HAS_ORACLE = True
except ImportError:
    HAS_ORACLE = False
    print("Warning: cx_Oracle not installed. Oracle monitoring will be simulated.")


class DatabaseService:
    """Service for Oracle database monitoring"""

    # Tablespace names that should be excluded from display
    # Only business data tablespaces and SYSTEM are shown
    EXCLUDED_TABLESPACES = {'USERS', 'TEMP', 'SYSAUX', 'UNDOTBS1', 'UNDOTBS2', 'UNDOTBS'}

    # SQL queries for monitoring
    TABLESPACE_QUERY = """
        SELECT
            tablespace_name,
            ROUND(used_space * 8192 / 1024 / 1024, 2) AS used_mb,
            ROUND(tablespace_size * 8192 / 1024 / 1024, 2) AS total_mb,
            ROUND(used_percent, 2) AS used_percent
        FROM dba_tablespace_usage_metrics
        WHERE tablespace_name IN ({tablespaces})
    """

    CONNECTION_QUERY = """
        SELECT
            COUNT(*) AS total_connections,
            SUM(CASE WHEN status = 'ACTIVE' THEN 1 ELSE 0 END) AS active_connections
        FROM v$session
        WHERE username IS NOT NULL
    """

    # Database cleanup SQL (referenced from db-cleanup skill)
    CLEANUP_QUERIES = {
        'delete_old_logs': """
            DELETE FROM ACC_LOG WHERE CREATE_TIME < SYSDATE - 90
        """,
        'delete_old_history': """
            DELETE FROM ACC_HISTORY WHERE CREATE_TIME < SYSDATE - 180
        """,
        'shrink_tablespace': """
            ALTER TABLESPACE {tablespace} SHRINK SPACE
        """
    }

    def __init__(self):
        self._connections: Dict[str, any] = {}

    def get_connection(self, server_id: str) -> Optional[any]:
        """Get or create Oracle connection for a server"""
        if not HAS_ORACLE:
            return None

        if server_id not in ORACLE_CONFIGS:
            return None

        config = ORACLE_CONFIGS[server_id]

        try:
            # Get password from environment variable
            password = os.environ.get(f'ORACLE_PASS_{server_id}', '')

            dsn = cx_Oracle.makedsn(
                config['host'],
                config['port'],
                service_name=config['service_name']
            )

            connection = cx_Oracle.connect(
                user=config['username'],
                password=password,
                dsn=dsn
            )

            return connection
        except Exception as e:
            print(f"Oracle connection error for {server_id}: {e}")
            return None

    def get_tablespace_status(self, server_id: str) -> List[Dict]:
        """Get tablespace usage for a server"""
        if server_id not in ORACLE_CONFIGS:
            return []

        config = ORACLE_CONFIGS[server_id]
        tablespaces = config.get('tablespaces', [])

        # Format tablespace names for SQL
        ts_list = ','.join([f"'{ts}'" for ts in tablespaces])
        query = self.TABLESPACE_QUERY.format(tablespaces=ts_list)

        conn = self.get_connection(server_id)
        results = []

        if conn:
            try:
                cursor = conn.cursor()
                cursor.execute(query)

                for row in cursor.fetchall():
                    ts_name, used_mb, total_mb, used_percent = row

                    # Determine status based on thresholds
                    if used_percent >= Config.TABLESPACE_CRITICAL_THRESHOLD:
                        status = 'critical'
                    elif used_percent >= Config.TABLESPACE_WARNING_THRESHOLD:
                        status = 'warning'
                    else:
                        status = 'normal'

                    results.append({
                        'name': ts_name,
                        'total_mb': total_mb,
                        'used_mb': used_mb,
                        'used_percent': used_percent,
                        'status': status,
                        'last_check': datetime.utcnow().isoformat()
                    })

                cursor.close()
            except Exception as e:
                print(f"Error querying tablespace for {server_id}: {e}")
            finally:
                conn.close()
        else:
            # Return simulated data if cannot connect
            for ts in tablespaces:
                results.append({
                    'name': ts,
                    'total_mb': 10240,
                    'used_mb': 5120,
                    'used_percent': 50.0,
                    'status': 'normal',
                    'last_check': datetime.utcnow().isoformat()
                })

        return results

    def get_connection_count(self, server_id: str) -> Dict:
        """Get active connection count for a database"""
        conn = self.get_connection(server_id)
        result = {
            'total_connections': 0,
            'active_connections': 0,
            'last_check': datetime.utcnow().isoformat()
        }

        if conn:
            try:
                cursor = conn.cursor()
                cursor.execute(self.CONNECTION_QUERY)
                row = cursor.fetchone()

                if row:
                    result['total_connections'] = row[0]
                    result['active_connections'] = row[1]

                cursor.close()
            except Exception as e:
                print(f"Error querying connections for {server_id}: {e}")
            finally:
                conn.close()

        return result

    def get_database_status(self, server_id: str) -> Dict:
        """Get comprehensive database status"""
        tablespaces = self.get_tablespace_status(server_id)
        connections = self.get_connection_count(server_id)

        # Determine overall status
        status = 'normal'
        for ts in tablespaces:
            if ts['status'] == 'critical':
                status = 'critical'
                break
            elif ts['status'] == 'warning' and status != 'critical':
                status = 'warning'

        return {
            'server_id': server_id,
            'status': status,
            'tablespaces': tablespaces,
            'connections': connections,
            'last_check': datetime.utcnow().isoformat()
        }

    @classmethod
    def is_business_tablespace(cls, ts_name: str) -> bool:
        """
        Check if a tablespace is a business data tablespace.
        Business tablespaces: ACC_DATA, IPLANT_*_DATA, etc.
        (names that do not match system keywords)
        """
        if not ts_name:
            return False
        name_upper = ts_name.upper()
        # Exclude known system tablespaces
        if name_upper in cls.EXCLUDED_TABLESPACES or name_upper == 'SYSTEM':
            return False
        if name_upper.startswith('UNDO'):
            return False
        return True

    @classmethod
    def is_system_tablespace(cls, ts_name: str) -> bool:
        """Check if a tablespace is the SYSTEM tablespace"""
        return ts_name and ts_name.upper() == 'SYSTEM'

    @classmethod
    def should_display_tablespace(cls, ts_name: str) -> bool:
        """
        Check if a tablespace should be displayed.
        Only business data tablespaces and SYSTEM are displayed.
        USERS, TEMP, SYSAUX, UNDOTBS etc. are filtered out.
        """
        return cls.is_business_tablespace(ts_name) or cls.is_system_tablespace(ts_name)

    @classmethod
    def filter_tablespaces(cls, all_tablespaces: List[Dict]) -> Dict:
        """
        Filter a list of tablespace dicts to show only business data
        tablespaces and SYSTEM tablespace.
        Returns a dict with business_tablespaces, primary_business,
        system_tablespace, and filtered_count.
        """
        business_tablespaces = []
        system_tablespace = None

        for ts in all_tablespaces:
            ts_name = ts.get('name', '')
            if cls.is_system_tablespace(ts_name):
                system_tablespace = ts
            elif cls.is_business_tablespace(ts_name):
                business_tablespaces.append(ts)

        # Find the primary business tablespace (highest usage)
        primary_business = None
        if business_tablespaces:
            primary_business = max(business_tablespaces, key=lambda t: t.get('used_percent', 0))

        filtered_count = len(business_tablespaces) + (1 if system_tablespace else 0)

        return {
            'business_tablespaces': business_tablespaces,
            'primary_business': primary_business,
            'system_tablespace': system_tablespace,
            'filtered_count': filtered_count
        }

    def get_all_databases_status(self) -> List[Dict]:
        """Get status of all monitored databases with filtered tablespace data"""
        results = []

        for server_id in ORACLE_CONFIGS.keys():
            # Get raw tablespace data and connections (single query per server)
            all_tablespaces = self.get_tablespace_status(server_id)
            connections = self.get_connection_count(server_id)

            # Filter tablespaces for display
            filtered = self.filter_tablespaces(all_tablespaces)

            # Determine overall status based on filtered tablespaces only
            display_tablespaces = filtered['business_tablespaces'][:]
            if filtered['system_tablespace']:
                display_tablespaces.append(filtered['system_tablespace'])

            status = 'normal'
            for ts in display_tablespaces:
                if ts['status'] == 'critical':
                    status = 'critical'
                    break
                elif ts['status'] == 'warning' and status != 'critical':
                    status = 'warning'

            results.append({
                'server_id': server_id,
                'status': status,
                'tablespaces': all_tablespaces,
                'business_tablespaces': filtered['business_tablespaces'],
                'primary_business': filtered['primary_business'],
                'system_tablespace': filtered['system_tablespace'],
                'filtered_tablespace_count': filtered['filtered_count'],
                'connections': connections,
                'last_check': datetime.utcnow().isoformat()
            })

        return results

    def run_cleanup(self, server_id: str, cleanup_type: str) -> Dict:
        """Run database cleanup operation"""
        if cleanup_type not in self.CLEANUP_QUERIES:
            return {
                'success': False,
                'error': f'Unknown cleanup type: {cleanup_type}'
            }

        conn = self.get_connection(server_id)
        if not conn:
            return {
                'success': False,
                'error': 'Cannot connect to database'
            }

        try:
            cursor = conn.cursor()
            query = self.CLEANUP_QUERIES[cleanup_type]

            # For tablespace operations, need to specify the tablespace
            if '{tablespace}' in query:
                # Get the primary tablespace
                config = ORACLE_CONFIGS.get(server_id, {})
                tablespaces = config.get('tablespaces', ['ACC_DATA'])
                query = query.format(tablespace=tablespaces[0])

            cursor.execute(query)
            conn.commit()
            rows_affected = cursor.rowcount

            cursor.close()
            conn.close()

            return {
                'success': True,
                'rows_affected': rows_affected,
                'cleanup_type': cleanup_type,
                'executed_at': datetime.utcnow().isoformat()
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }

    def optimize_tablespace(self, server_id: str, tablespace_name: str = None) -> Dict:
        """One-click tablespace optimization"""
        results = []

        # Step 1: Delete old logs
        log_result = self.run_cleanup(server_id, 'delete_old_logs')
        results.append({'operation': 'delete_old_logs', **log_result})

        # Step 2: Delete old history
        history_result = self.run_cleanup(server_id, 'delete_old_history')
        results.append({'operation': 'delete_old_history', **history_result})

        # Step 3: Shrink tablespace (if supported)
        # Note: This requires specific privileges

        success = all(r.get('success', False) for r in results)

        return {
            'success': success,
            'server_id': server_id,
            'operations': results,
            'executed_at': datetime.utcnow().isoformat()
        }

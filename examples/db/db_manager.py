#!/usr/bin/env python3
"""
TLS 테스트 추적 시스템 DB 매니저
- CRUD 작업 간소화
- 자동 타임스탬프 처리 (KST)
- 트랜잭션 지원
"""
import pymysql
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from contextlib import contextmanager

# DB 연결 정보
DB_CONFIG = {
    'host': '220.121.120.83',
    'user': 'tls_user',
    'password': 'TLS_Pass_2024!@',
    'database': 'tls',
    'charset': 'utf8mb4',
    'cursorclass': pymysql.cursors.DictCursor
}

class DBManager:
    """TLS 테스트 추적 시스템 DB 매니저"""

    def __init__(self, config=None):
        """초기화"""
        self.config = config or DB_CONFIG
        self._conn = None

    @contextmanager
    def get_connection(self):
        """DB 연결 (context manager)"""
        conn = pymysql.connect(**self.config)
        try:
            yield conn
        finally:
            conn.close()

    @staticmethod
    def now_kst():
        """현재 한국 시간"""
        return datetime.now() + timedelta(hours=9)

    # ========================================================================
    # Fingerprints 관련
    # ========================================================================

    def insert_fingerprint(self, data: Dict) -> int:
        """TLS 핑거프린트 저장"""
        with self.get_connection() as conn:
            with conn.cursor() as cursor:
                sql = """
                    INSERT INTO fingerprints (
                        device_name, os_version, browser_name, browser_version,
                        collected_at, browserstack_session_id, collection_ip,
                        ja3_hash, ja3_text, ja4, akamai_hash, akamai_text,
                        http2_settings, http2_priority,
                        tls_version, cipher_suites, tls_extensions,
                        signature_algorithms, supported_groups,
                        user_agent, raw_tls_data, tls_html_snapshot,
                        notes, is_active
                    ) VALUES (
                        %(device_name)s, %(os_version)s, %(browser_name)s, %(browser_version)s,
                        %(collected_at)s, %(browserstack_session_id)s, %(collection_ip)s,
                        %(ja3_hash)s, %(ja3_text)s, %(ja4)s, %(akamai_hash)s, %(akamai_text)s,
                        %(http2_settings)s, %(http2_priority)s,
                        %(tls_version)s, %(cipher_suites)s, %(tls_extensions)s,
                        %(signature_algorithms)s, %(supported_groups)s,
                        %(user_agent)s, %(raw_tls_data)s, %(tls_html_snapshot)s,
                        %(notes)s, %(is_active)s
                    )
                """

                # 기본값 설정
                params = {
                    'collected_at': data.get('collected_at', self.now_kst()),
                    'is_active': data.get('is_active', True),
                    **data
                }

                cursor.execute(sql, params)
                conn.commit()
                return cursor.lastrowid

    def get_fingerprint(self, fingerprint_id: int) -> Optional[Dict]:
        """핑거프린트 조회"""
        with self.get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    "SELECT * FROM fingerprints WHERE id = %s",
                    (fingerprint_id,)
                )
                return cursor.fetchone()

    def get_latest_fingerprint(self, device_name: str = None) -> Optional[Dict]:
        """최신 핑거프린트 조회"""
        with self.get_connection() as conn:
            with conn.cursor() as cursor:
                if device_name:
                    cursor.execute("""
                        SELECT * FROM fingerprints
                        WHERE device_name = %s AND is_active = TRUE
                        ORDER BY collected_at DESC
                        LIMIT 1
                    """, (device_name,))
                else:
                    cursor.execute("""
                        SELECT * FROM fingerprints
                        WHERE is_active = TRUE
                        ORDER BY collected_at DESC
                        LIMIT 1
                    """)
                return cursor.fetchone()

    def list_fingerprints(self, limit: int = 50, active_only: bool = True) -> List[Dict]:
        """핑거프린트 목록"""
        with self.get_connection() as conn:
            with conn.cursor() as cursor:
                sql = "SELECT * FROM fingerprints"
                if active_only:
                    sql += " WHERE is_active = TRUE"
                sql += " ORDER BY collected_at DESC LIMIT %s"

                cursor.execute(sql, (limit,))
                return cursor.fetchall()

    # ========================================================================
    # Cookies 관련
    # ========================================================================

    def insert_cookies(self, data: Dict) -> int:
        """쿠키 세트 저장"""
        with self.get_connection() as conn:
            with conn.cursor() as cursor:
                sql = """
                    INSERT INTO cookies (
                        fingerprint_id, collected_at, source_url, trace_id,
                        cookies_json, cookie_count, has_cto_bundle,
                        usage_count, last_used_at, expired_at,
                        is_valid, notes
                    ) VALUES (
                        %(fingerprint_id)s, %(collected_at)s, %(source_url)s, %(trace_id)s,
                        %(cookies_json)s, %(cookie_count)s, %(has_cto_bundle)s,
                        %(usage_count)s, %(last_used_at)s, %(expired_at)s,
                        %(is_valid)s, %(notes)s
                    )
                """

                params = {
                    'collected_at': data.get('collected_at', self.now_kst()),
                    'usage_count': data.get('usage_count', 0),
                    'is_valid': data.get('is_valid', True),
                    **data
                }

                cursor.execute(sql, params)
                conn.commit()
                return cursor.lastrowid

    def get_cookies(self, cookie_id: int) -> Optional[Dict]:
        """쿠키 세트 조회"""
        with self.get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("SELECT * FROM cookies WHERE id = %s", (cookie_id,))
                return cursor.fetchone()

    def increment_cookie_usage(self, cookie_id: int):
        """쿠키 사용 횟수 증가"""
        with self.get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("""
                    UPDATE cookies
                    SET usage_count = usage_count + 1,
                        last_used_at = %s
                    WHERE id = %s
                """, (self.now_kst(), cookie_id))
                conn.commit()

    def mark_cookie_invalid(self, cookie_id: int):
        """쿠키 무효 처리"""
        with self.get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("""
                    UPDATE cookies
                    SET is_valid = FALSE,
                        expired_at = %s
                    WHERE id = %s
                """, (self.now_kst(), cookie_id))
                conn.commit()

    # ========================================================================
    # Test Executions 관련
    # ========================================================================

    def insert_test_execution(self, data: Dict) -> int:
        """테스트 실행 기록"""
        with self.get_connection() as conn:
            with conn.cursor() as cursor:
                sql = """
                    INSERT INTO test_executions (
                        fingerprint_id, cookie_id, test_type, test_name, executed_at,
                        source_ip, vpn_server_ip, proxy_server,
                        url, method, headers_json,
                        ja3_used, akamai_used, extra_fp_json,
                        status_code, response_time_ms, response_size_bytes, response_headers_json,
                        success, blocked, has_product_list, product_count,
                        response_html, response_preview,
                        error_message, error_type,
                        script_file, notes
                    ) VALUES (
                        %(fingerprint_id)s, %(cookie_id)s, %(test_type)s, %(test_name)s, %(executed_at)s,
                        %(source_ip)s, %(vpn_server_ip)s, %(proxy_server)s,
                        %(url)s, %(method)s, %(headers_json)s,
                        %(ja3_used)s, %(akamai_used)s, %(extra_fp_json)s,
                        %(status_code)s, %(response_time_ms)s, %(response_size_bytes)s, %(response_headers_json)s,
                        %(success)s, %(blocked)s, %(has_product_list)s, %(product_count)s,
                        %(response_html)s, %(response_preview)s,
                        %(error_message)s, %(error_type)s,
                        %(script_file)s, %(notes)s
                    )
                """

                params = {
                    'executed_at': data.get('executed_at', self.now_kst()),
                    'method': data.get('method', 'GET'),
                    **data
                }

                cursor.execute(sql, params)
                conn.commit()

                # 쿠키 사용 횟수 증가
                if data.get('cookie_id'):
                    self.increment_cookie_usage(data['cookie_id'])

                return cursor.lastrowid

    def get_test_execution(self, test_id: int) -> Optional[Dict]:
        """테스트 실행 조회"""
        with self.get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("""
                    SELECT te.*,
                           f.device_name,
                           c.cookie_count,
                           c.has_cto_bundle
                    FROM test_executions te
                    JOIN fingerprints f ON te.fingerprint_id = f.id
                    LEFT JOIN cookies c ON te.cookie_id = c.id
                    WHERE te.id = %s
                """, (test_id,))
                return cursor.fetchone()

    def list_test_executions(
        self,
        limit: int = 100,
        success_only: bool = False,
        failed_only: bool = False
    ) -> List[Dict]:
        """테스트 실행 목록"""
        with self.get_connection() as conn:
            with conn.cursor() as cursor:
                sql = """
                    SELECT te.*,
                           f.device_name,
                           c.cookie_count
                    FROM test_executions te
                    JOIN fingerprints f ON te.fingerprint_id = f.id
                    LEFT JOIN cookies c ON te.cookie_id = c.id
                """

                if success_only:
                    sql += " WHERE te.success = TRUE"
                elif failed_only:
                    sql += " WHERE te.success = FALSE"

                sql += " ORDER BY te.executed_at DESC LIMIT %s"

                cursor.execute(sql, (limit,))
                return cursor.fetchall()

    # ========================================================================
    # Test Comparisons 관련
    # ========================================================================

    def insert_test_comparison(self, data: Dict) -> int:
        """테스트 비교 기록"""
        with self.get_connection() as conn:
            with conn.cursor() as cursor:
                sql = """
                    INSERT INTO test_comparisons (
                        fingerprint_id, cookie_id,
                        browserstack_session_id, browserstack_success, browserstack_html_size,
                        browserstack_screenshot, browserstack_timestamp,
                        curlcffi_execution_id, curlcffi_success, curlcffi_html_size,
                        curlcffi_timestamp,
                        time_diff_seconds, ip_same, cookies_same, headers_diff,
                        analysis_result, root_cause
                    ) VALUES (
                        %(fingerprint_id)s, %(cookie_id)s,
                        %(browserstack_session_id)s, %(browserstack_success)s, %(browserstack_html_size)s,
                        %(browserstack_screenshot)s, %(browserstack_timestamp)s,
                        %(curlcffi_execution_id)s, %(curlcffi_success)s, %(curlcffi_html_size)s,
                        %(curlcffi_timestamp)s,
                        %(time_diff_seconds)s, %(ip_same)s, %(cookies_same)s, %(headers_diff)s,
                        %(analysis_result)s, %(root_cause)s
                    )
                """

                cursor.execute(sql, data)
                conn.commit()
                return cursor.lastrowid

    # ========================================================================
    # Daily Summary 관련
    # ========================================================================

    def update_daily_summary(self, date=None):
        """일일 요약 업데이트"""
        if date is None:
            date = self.now_kst().date()

        with self.get_connection() as conn:
            with conn.cursor() as cursor:
                # 오늘의 통계 계산
                cursor.execute("""
                    SELECT
                        COUNT(DISTINCT f.id) as fingerprints,
                        COUNT(DISTINCT c.id) as cookies,
                        COUNT(te.id) as total_tests,
                        SUM(CASE WHEN te.success THEN 1 ELSE 0 END) as successful,
                        SUM(CASE WHEN NOT te.success THEN 1 ELSE 0 END) as failed,
                        SUM(CASE WHEN te.blocked THEN 1 ELSE 0 END) as blocked,
                        SUM(CASE WHEN f.device_name LIKE '%%iPhone%%' THEN 1 ELSE 0 END) as iphone,
                        SUM(CASE WHEN f.device_name LIKE '%%Galaxy%%' OR f.device_name LIKE '%%Android%%' THEN 1 ELSE 0 END) as android,
                        SUM(CASE WHEN te.test_type = 'DIRECT' THEN 1 ELSE 0 END) as direct,
                        SUM(CASE WHEN te.test_type = 'VPN' THEN 1 ELSE 0 END) as vpn,
                        SUM(CASE WHEN te.test_type = 'PROXY' THEN 1 ELSE 0 END) as proxy
                    FROM test_executions te
                    JOIN fingerprints f ON te.fingerprint_id = f.id
                    LEFT JOIN cookies c ON te.cookie_id = c.id
                    WHERE DATE(te.executed_at) = %s
                """, (date,))

                stats = cursor.fetchone()

                # 성공률 계산
                total = int(stats['total_tests'] or 0)
                successful = int(stats['successful'] or 0)
                success_rate = (successful * 100.0 / total) if total > 0 else 0

                # UPSERT (INSERT OR UPDATE)
                cursor.execute("""
                    INSERT INTO daily_summary (
                        summary_date,
                        fingerprints_collected, cookies_collected,
                        total_tests, successful_tests, failed_tests, blocked_tests,
                        success_rate,
                        iphone_tests, android_tests,
                        direct_tests, vpn_tests, proxy_tests
                    ) VALUES (
                        %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                    )
                    ON DUPLICATE KEY UPDATE
                        fingerprints_collected = VALUES(fingerprints_collected),
                        cookies_collected = VALUES(cookies_collected),
                        total_tests = VALUES(total_tests),
                        successful_tests = VALUES(successful_tests),
                        failed_tests = VALUES(failed_tests),
                        blocked_tests = VALUES(blocked_tests),
                        success_rate = VALUES(success_rate),
                        iphone_tests = VALUES(iphone_tests),
                        android_tests = VALUES(android_tests),
                        direct_tests = VALUES(direct_tests),
                        vpn_tests = VALUES(vpn_tests),
                        proxy_tests = VALUES(proxy_tests)
                """, (
                    date,
                    stats['fingerprints'], stats['cookies'],
                    stats['total_tests'], stats['successful'], stats['failed'], stats['blocked'],
                    success_rate,
                    stats['iphone'], stats['android'],
                    stats['direct'], stats['vpn'], stats['proxy']
                ))

                conn.commit()

    def get_daily_summary(self, days: int = 7) -> List[Dict]:
        """일일 요약 조회"""
        with self.get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("""
                    SELECT *
                    FROM daily_summary
                    WHERE summary_date >= DATE_SUB(CURDATE(), INTERVAL %s DAY)
                    ORDER BY summary_date DESC
                """, (days,))
                return cursor.fetchall()

    # ========================================================================
    # 분석 쿼리
    # ========================================================================

    def get_success_rate_by_device(self) -> List[Dict]:
        """디바이스별 성공률"""
        with self.get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("""
                    SELECT
                        f.device_name,
                        COUNT(*) as total_tests,
                        SUM(CASE WHEN te.success THEN 1 ELSE 0 END) as successful_tests,
                        ROUND(SUM(CASE WHEN te.success THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 2) as success_rate
                    FROM test_executions te
                    JOIN fingerprints f ON te.fingerprint_id = f.id
                    GROUP BY f.device_name
                    ORDER BY success_rate DESC
                """)
                return cursor.fetchall()

    def get_cookie_usage_stats(self, cookie_id: int) -> Dict:
        """쿠키 사용 통계"""
        with self.get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("""
                    SELECT
                        c.id,
                        c.cookie_count,
                        c.has_cto_bundle,
                        c.usage_count,
                        c.is_valid,
                        COUNT(te.id) as test_count,
                        SUM(CASE WHEN te.success THEN 1 ELSE 0 END) as success_count,
                        MIN(te.executed_at) as first_used,
                        MAX(te.executed_at) as last_used
                    FROM cookies c
                    LEFT JOIN test_executions te ON c.id = te.cookie_id
                    WHERE c.id = %s
                    GROUP BY c.id
                """, (cookie_id,))
                return cursor.fetchone()


# 전역 인스턴스
_db_manager = None

def get_db_manager() -> DBManager:
    """DB 매니저 싱글톤"""
    global _db_manager
    if _db_manager is None:
        _db_manager = DBManager()
    return _db_manager

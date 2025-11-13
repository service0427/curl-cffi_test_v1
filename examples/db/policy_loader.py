#!/usr/bin/env python3
"""
DB 기반 정책 로더
- CLAUDE.md가 너무 길어서 Claude가 놓치는 부분 방지
- 필요한 정책을 DB에서 동적으로 로드
- Python 파일로 쉽게 import하여 사용
"""
import sys
sys.path.insert(0, '/home/tech/test')

from db.db_manager import get_db_manager
from typing import Dict, List, Optional

class PolicyLoader:
    """정책 로더 - DB에서 정책을 조회하여 제공"""

    def __init__(self):
        self.db = get_db_manager()
        self._policies = None

    def load_all_policies(self) -> Dict:
        """모든 정책 한 번에 로드 (캐싱)"""
        if self._policies is not None:
            return self._policies

        policies = {}

        with self.db.get_connection() as conn:
            with conn.cursor() as cursor:
                # 정책 테이블에서 모든 정책 조회
                cursor.execute("""
                    SELECT policy_key, policy_value, description
                    FROM project_policies
                    WHERE is_active = TRUE
                    ORDER BY category, priority
                """)
                rows = cursor.fetchall()

                for row in rows:
                    policies[row['policy_key']] = {
                        'value': row['policy_value'],
                        'description': row['description']
                    }

        self._policies = policies
        return policies

    def get_policy(self, key: str, default=None):
        """특정 정책 조회"""
        policies = self.load_all_policies()
        policy = policies.get(key)
        return policy['value'] if policy else default

    def get_cookie_limit(self) -> int:
        """쿠키 사용 횟수 제한"""
        return int(self.get_policy('cookie_usage_limit', 10))

    def get_test_interval(self) -> int:
        """테스트 간 대기 시간 (초)"""
        return int(self.get_policy('test_interval_seconds', 15))

    def get_required_cookies(self) -> List[str]:
        """필수 쿠키 목록"""
        value = self.get_policy('required_cookies', 'cto_bundle')
        return [c.strip() for c in value.split(',')]

    def get_browserstack_local_required(self) -> bool:
        """BrowserStack Local 필수 여부"""
        return self.get_policy('browserstack_local_required', 'true').lower() == 'true'

    def get_five_way_matching_required(self) -> bool:
        """5-way 매칭 필수 여부 (TLS+HTTP2+Headers+IP+Cookies)"""
        return self.get_policy('five_way_matching_required', 'true').lower() == 'true'

    def get_vpn_api_url(self) -> str:
        """VPN API URL"""
        return self.get_policy('vpn_api_url', 'http://220.121.120.83/vpn_api')

    def get_archive_after_days(self) -> int:
        """테스트 결과 아카이브 기준 (일)"""
        return int(self.get_policy('archive_test_results_after_days', 30))

    def should_use_extra_fp(self) -> bool:
        """extra_fp 사용 여부"""
        return self.get_policy('use_extra_fp', 'true').lower() == 'true'

    def should_use_sec_fetch_headers(self) -> bool:
        """Sec-Fetch 헤더 사용 여부"""
        return self.get_policy('use_sec_fetch_headers', 'true').lower() == 'true'

    def get_recommended_devices(self) -> List[str]:
        """추천 디바이스 목록"""
        value = self.get_policy('recommended_devices', 'iPhone 15 Pro,Samsung Galaxy S23')
        return [d.strip() for d in value.split(',')]

    def print_all_policies(self):
        """모든 정책 출력 (디버깅용)"""
        policies = self.load_all_policies()

        print("=" * 80)
        print("📋 프로젝트 정책 (DB 로드)")
        print("=" * 80)
        print()

        for key, policy in policies.items():
            print(f"• {key}")
            print(f"  값: {policy['value']}")
            print(f"  설명: {policy['description']}")
            print()


# 싱글톤 인스턴스
_policy_loader = None

def get_policy_loader() -> PolicyLoader:
    """PolicyLoader 싱글톤 인스턴스 반환"""
    global _policy_loader
    if _policy_loader is None:
        _policy_loader = PolicyLoader()
    return _policy_loader


if __name__ == "__main__":
    # 테스트 실행
    loader = get_policy_loader()
    loader.print_all_policies()

    print("=" * 80)
    print("주요 정책 값:")
    print("=" * 80)
    print(f"쿠키 사용 제한: {loader.get_cookie_limit()}회")
    print(f"테스트 간격: {loader.get_test_interval()}초")
    print(f"필수 쿠키: {loader.get_required_cookies()}")
    print(f"BrowserStack Local 필수: {loader.get_browserstack_local_required()}")
    print(f"5-way 매칭 필수: {loader.get_five_way_matching_required()}")
    print(f"VPN API URL: {loader.get_vpn_api_url()}")

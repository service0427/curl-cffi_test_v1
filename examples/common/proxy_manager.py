#!/usr/bin/env python3
"""
프록시 관리 공통 모듈
- SOCKS5 모바일 프록시 관리
- 자동 토글 프록시 (120초마다 IP 변경)
- 랜덤 선택 및 상태 관리
"""
import requests
import random
from typing import Optional, Dict, List
from datetime import datetime
from curl_cffi import requests as cf_requests

# 프록시 API 설정
PROXY_API_URL = "http://mkt.techb.kr:3001/api/proxy/status"
DEFAULT_REMAIN_SECONDS = 120


class ProxyManager:
    """프록시 관리 클래스"""

    def __init__(self, api_url: str = PROXY_API_URL):
        """
        ProxyManager 초기화

        Args:
            api_url: 프록시 API URL
        """
        self.api_url = api_url
        self.last_fetch_time = None
        self.cached_proxies = []

    def fetch_proxies(self, remain_seconds: int = DEFAULT_REMAIN_SECONDS) -> List[Dict]:
        """
        프록시 목록 조회

        Args:
            remain_seconds: 최소 남은 시간 (초)

        Returns:
            프록시 정보 리스트
        """
        try:
            url = f"{self.api_url}?remain={remain_seconds}"
            resp = requests.get(url, timeout=10).json()

            if resp.get('success'):
                proxies = resp.get('proxies', [])
                self.cached_proxies = proxies
                self.last_fetch_time = datetime.now()
                return proxies
            else:
                print("❌ 프록시 목록 조회 실패")
                return []

        except Exception as e:
            print(f"⚠️  프록시 조회 중 오류: {str(e)[:50]}")
            return []

    def get_random_proxy(self, remain_seconds: int = DEFAULT_REMAIN_SECONDS) -> Optional[Dict]:
        """
        랜덤 프록시 선택

        Args:
            remain_seconds: 최소 남은 시간 (초)

        Returns:
            프록시 정보 딕셔너리 또는 None
            {
                'proxy': '14.37.117.98:10025',
                'external_ip': '110.70.26.78',
                'use_count': 1,
                'remaining_work_seconds': '176'
            }
        """
        proxies = self.fetch_proxies(remain_seconds)

        if not proxies:
            return None

        # 사용 횟수가 적은 순으로 정렬 후 랜덤 선택
        proxies.sort(key=lambda p: int(p.get('use_count', 999)))

        # 상위 50% 중에서 랜덤 선택 (사용 횟수 적은 것 우선)
        top_half = proxies[:max(1, len(proxies) // 2)]
        selected = random.choice(top_half)

        return selected

    def get_least_used_proxy(self, remain_seconds: int = DEFAULT_REMAIN_SECONDS) -> Optional[Dict]:
        """
        가장 덜 사용된 프록시 선택

        Args:
            remain_seconds: 최소 남은 시간 (초)

        Returns:
            프록시 정보 딕셔너리 또는 None
        """
        proxies = self.fetch_proxies(remain_seconds)

        if not proxies:
            return None

        # 사용 횟수가 가장 적은 것 선택
        proxies.sort(key=lambda p: int(p.get('use_count', 999)))
        return proxies[0]

    def get_proxies_by_remaining_time(
        self,
        min_seconds: int = DEFAULT_REMAIN_SECONDS,
        max_seconds: int = None
    ) -> List[Dict]:
        """
        남은 시간 범위로 프록시 필터링

        Args:
            min_seconds: 최소 남은 시간
            max_seconds: 최대 남은 시간 (None이면 제한 없음)

        Returns:
            필터링된 프록시 리스트
        """
        proxies = self.fetch_proxies(min_seconds)

        if max_seconds:
            proxies = [
                p for p in proxies
                if int(p.get('remaining_work_seconds', 0)) <= max_seconds
            ]

        return proxies

    def format_proxy_for_curl(self, proxy_info: Dict) -> str:
        """
        curl-cffi용 프록시 문자열 생성

        Args:
            proxy_info: 프록시 정보 딕셔너리

        Returns:
            프록시 문자열 (예: "socks5://14.37.117.98:10025")
        """
        if not proxy_info:
            return None

        proxy = proxy_info.get('proxy', '')
        return f"socks5://{proxy}"

    def format_proxy_for_requests(self, proxy_info: Dict) -> Dict[str, str]:
        """
        requests용 프록시 딕셔너리 생성

        Args:
            proxy_info: 프록시 정보 딕셔너리

        Returns:
            프록시 딕셔너리 (예: {'http': 'socks5://...', 'https': 'socks5://...'})
        """
        if not proxy_info:
            return None

        proxy = proxy_info.get('proxy', '')
        proxy_url = f"socks5://{proxy}"

        return {
            'http': proxy_url,
            'https': proxy_url
        }

    def get_current_ip_via_proxy(self, proxy_info: Dict) -> str:
        """
        프록시를 통한 현재 IP 확인 (curl-cffi 사용)

        Args:
            proxy_info: 프록시 정보 딕셔너리

        Returns:
            IP 주소 문자열
        """
        try:
            proxy_url = self.format_proxy_for_curl(proxy_info)

            resp = cf_requests.get(
                "https://api.ipify.org?format=json",
                proxies={'https': proxy_url},
                timeout=10
            )

            return resp.json()['ip']

        except Exception as e:
            return f"Error: {str(e)[:50]}"

    def verify_proxy(self, proxy_info: Dict) -> Dict:
        """
        프록시 작동 확인

        Args:
            proxy_info: 프록시 정보 딕셔너리

        Returns:
            검증 결과 딕셔너리
        """
        current_ip = self.get_current_ip_via_proxy(proxy_info)
        expected_ip = proxy_info.get('external_ip', '')

        result = {
            'proxy': proxy_info.get('proxy'),
            'expected_ip': expected_ip,
            'actual_ip': current_ip,
            'working': current_ip == expected_ip,
            'error': current_ip.startswith('Error')
        }

        return result

    def print_status(self, remain_seconds: int = DEFAULT_REMAIN_SECONDS):
        """프록시 상태 출력"""
        proxies = self.fetch_proxies(remain_seconds)

        print("="*80)
        print(f"프록시 서버 상태 (최소 {remain_seconds}초 이상 남은 것)")
        print("="*80)
        print()

        if not proxies:
            print("⚠️  사용 가능한 프록시가 없습니다!")
            return

        print(f"총 사용 가능한 프록시: {len(proxies)}개")
        print()

        # 사용 횟수별 통계
        use_counts = {}
        for p in proxies:
            count = int(p.get('use_count', 0))
            use_counts[count] = use_counts.get(count, 0) + 1

        print("사용 횟수별 분포:")
        for count in sorted(use_counts.keys()):
            print(f"  {count}회 사용: {use_counts[count]}개")
        print()

        # 상위 10개 프록시 상세 정보
        print("프록시 상세 정보 (사용 횟수 적은 순):")
        print(f"{'프록시':<25} {'외부 IP':<18} {'사용횟수':<8} {'남은시간':<8}")
        print("-"*80)

        proxies.sort(key=lambda p: int(p.get('use_count', 999)))

        for i, proxy in enumerate(proxies[:10]):
            proxy_addr = proxy.get('proxy', '')
            external_ip = proxy.get('external_ip', '')
            use_count = proxy.get('use_count', 0)
            remaining = proxy.get('remaining_work_seconds', 0)

            print(f"{proxy_addr:<25} {external_ip:<18} {use_count:<8} {remaining}초")

        if len(proxies) > 10:
            print(f"... 외 {len(proxies) - 10}개")

        print()

        # 권장 사항
        min_use_count = min(int(p.get('use_count', 0)) for p in proxies)
        max_use_count = max(int(p.get('use_count', 0)) for p in proxies)

        if max_use_count - min_use_count > 5:
            print("⚠️  일부 프록시의 사용 횟수가 많습니다. 균등 분배 권장.")
        else:
            print("✅ 프록시 사용이 비교적 균등합니다.")


class ProxyConnection:
    """
    프록시 연결 Context Manager

    사용 예시:
        with ProxyConnection() as proxy:
            if proxy:
                print(f"연결된 IP: {proxy['external_ip']}")
                # 작업 수행...
    """

    def __init__(self, manager: ProxyManager = None, remain_seconds: int = DEFAULT_REMAIN_SECONDS):
        self.manager = manager or ProxyManager()
        self.remain_seconds = remain_seconds
        self.proxy_info = None

    def __enter__(self):
        self.proxy_info = self.manager.get_random_proxy(self.remain_seconds)
        return self.proxy_info

    def __exit__(self, exc_type, exc_val, exc_tb):
        # 프록시는 자동 관리되므로 명시적 해제 불필요
        return False


# 편의 함수들

def get_random_proxy(remain_seconds: int = DEFAULT_REMAIN_SECONDS) -> Optional[Dict]:
    """
    랜덤 프록시 선택 (전역 함수)

    Args:
        remain_seconds: 최소 남은 시간 (초)

    Returns:
        프록시 정보 딕셔너리 또는 None
    """
    manager = ProxyManager()
    return manager.get_random_proxy(remain_seconds)


def get_least_used_proxy(remain_seconds: int = DEFAULT_REMAIN_SECONDS) -> Optional[Dict]:
    """
    가장 덜 사용된 프록시 선택 (전역 함수)

    Args:
        remain_seconds: 최소 남은 시간 (초)

    Returns:
        프록시 정보 딕셔너리 또는 None
    """
    manager = ProxyManager()
    return manager.get_least_used_proxy(remain_seconds)


def fetch_proxies(remain_seconds: int = DEFAULT_REMAIN_SECONDS) -> List[Dict]:
    """
    프록시 목록 조회 (전역 함수)

    Args:
        remain_seconds: 최소 남은 시간 (초)

    Returns:
        프록시 리스트
    """
    manager = ProxyManager()
    return manager.fetch_proxies(remain_seconds)


def format_proxy_for_curl(proxy_info: Dict) -> str:
    """
    curl-cffi용 프록시 문자열 생성 (전역 함수)

    Args:
        proxy_info: 프록시 정보 딕셔너리

    Returns:
        프록시 문자열 (예: "socks5://14.37.117.98:10025")
    """
    manager = ProxyManager()
    return manager.format_proxy_for_curl(proxy_info)


def format_proxy_for_requests(proxy_info: Dict) -> Dict[str, str]:
    """
    requests용 프록시 딕셔너리 생성 (전역 함수)

    Args:
        proxy_info: 프록시 정보 딕셔너리

    Returns:
        프록시 딕셔너리
    """
    manager = ProxyManager()
    return manager.format_proxy_for_requests(proxy_info)


def verify_proxy(proxy_info: Dict) -> Dict:
    """
    프록시 작동 확인 (전역 함수)

    Args:
        proxy_info: 프록시 정보 딕셔너리

    Returns:
        검증 결과 딕셔너리
    """
    manager = ProxyManager()
    return manager.verify_proxy(proxy_info)


def print_proxy_status(remain_seconds: int = DEFAULT_REMAIN_SECONDS):
    """프록시 서버 상태 출력 (전역 함수)"""
    manager = ProxyManager()
    manager.print_status(remain_seconds)


if __name__ == "__main__":
    # 테스트 코드
    print("Proxy Manager 테스트")
    print()

    # 프록시 상태 확인
    print_proxy_status()
    print()

    # 랜덤 프록시 선택 테스트
    print("랜덤 프록시 선택:")
    proxy = get_random_proxy()
    if proxy:
        print(f"  프록시: {proxy['proxy']}")
        print(f"  외부 IP: {proxy['external_ip']}")
        print(f"  사용 횟수: {proxy['use_count']}")
        print(f"  남은 시간: {proxy['remaining_work_seconds']}초")
        print()

        # 프록시 검증
        print("프록시 검증 중...")
        result = verify_proxy(proxy)
        if result['working']:
            print(f"  ✅ 프록시 작동 정상")
            print(f"  예상 IP: {result['expected_ip']}")
            print(f"  실제 IP: {result['actual_ip']}")
        else:
            print(f"  ❌ 프록시 작동 실패")
            print(f"  예상 IP: {result['expected_ip']}")
            print(f"  실제 IP: {result['actual_ip']}")
    else:
        print("  ❌ 사용 가능한 프록시 없음")

    print("\n테스트 완료")

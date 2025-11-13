#!/usr/bin/env python3
"""
VPN 관리 공통 모듈
- WireGuard VPN 할당, 연결, 해제, 반납
- IP 확인 및 모니터링
- 중복 방지 및 에러 처리

⚠️ 중요: curl-cffi 테스트 시 VPN 필수!
========================================
- curl-cffi로 Coupang 테스트 시 서버 IP가 블랙리스트에 등록될 수 있음
- VPNConnection context manager를 사용하여 IP를 변경해야 함
- 성공 사례: VPN 사용 시 7~10회 연속 성공 확인됨

사용 예시:
    from common.vpn_manager import VPNConnection

    with VPNConnection() as vpn:
        if vpn:
            # curl-cffi 테스트 수행
            response = cf_requests.get(url, cookies=cookies_dict, ...)
"""
import requests
import subprocess
import tempfile
import time
from pathlib import Path
from typing import Optional, Dict, List
from curl_cffi import requests as cf_requests

# VPN API 설정
VPN_API = "http://220.121.120.83/vpn_api"
SUDO_PW = "Tech1324!"

# 할당된 VPN 키 추적 (중복 방지)
_allocated_keys = set()


class VPNManager:
    """VPN 연결 관리 클래스"""

    def __init__(self, api_url: str = VPN_API, sudo_password: str = SUDO_PW):
        """
        VPNManager 초기화

        Args:
            api_url: VPN API 베이스 URL
            sudo_password: sudo 비밀번호
        """
        self.api_url = api_url
        self.sudo_password = sudo_password
        self.allocated_keys = set()

    def get_available_servers(self) -> List[Dict]:
        """
        사용 가능한 VPN 서버 목록 조회

        Returns:
            사용 가능한 서버 목록
        """
        try:
            resp = requests.get(f"{self.api_url}/list", timeout=10).json()
            if resp.get('success'):
                return resp.get('available_servers', [])
        except Exception as e:
            print(f"⚠️  서버 목록 조회 실패: {str(e)[:50]}")
        return []

    def get_server_status(self) -> Dict:
        """
        VPN 서버 상태 전체 조회

        Returns:
            서버 상태 정보 딕셔너리
        """
        try:
            resp = requests.get(f"{self.api_url}/list", timeout=10).json()
            if resp.get('success'):
                return {
                    'success': True,
                    'servers': resp.get('available_servers', []),
                    'total_available': resp.get('total_available', 0)
                }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }

    def allocate(self) -> Optional[Dict]:
        """
        VPN 서버 할당 및 연결

        Returns:
            VPN 정보 딕셔너리 또는 None (실패 시)
            {
                'config_file': str,
                'public_key': str,
                'server_ip': str,
                'internal_ip': str
            }
        """
        try:
            # VPN 서버 할당
            vpn = requests.get(f"{self.api_url}/allocate", timeout=10).json()

            if not vpn.get('success'):
                print("❌ VPN 할당 실패")
                return None

            public_key = vpn['public_key']

            # 중복 체크
            if public_key in self.allocated_keys or public_key in _allocated_keys:
                print(f"⚠️  이미 할당된 키: {public_key[:20]}...")
                return None

            # WireGuard 설정 파일 생성
            with tempfile.NamedTemporaryFile(mode='w', suffix='.conf', delete=False) as f:
                f.write(vpn['config'])
                cfg_file = f.name

            # VPN 연결
            cmd = f"echo '{self.sudo_password}' | sudo -S wg-quick up {cfg_file}"
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True)

            if result.returncode != 0:
                print(f"❌ VPN 연결 실패: {result.stderr[:100]}")
                Path(cfg_file).unlink(missing_ok=True)
                return None

            # 할당 키 추적
            self.allocated_keys.add(public_key)
            _allocated_keys.add(public_key)

            vpn_info = {
                'config_file': cfg_file,
                'public_key': public_key,
                'server_ip': vpn['server_ip'],
                'internal_ip': vpn.get('internal_ip', '')
            }

            return vpn_info

        except Exception as e:
            print(f"❌ VPN 할당 중 오류: {str(e)[:100]}")
            return None

    def release(self, vpn_info: Dict) -> bool:
        """
        VPN 연결 해제 및 반납

        Args:
            vpn_info: allocate()에서 반환된 VPN 정보

        Returns:
            성공 여부
        """
        try:
            # WireGuard 연결 해제
            cmd = f"echo '{self.sudo_password}' | sudo -S wg-quick down {vpn_info['config_file']}"
            subprocess.run(cmd, shell=True, capture_output=True, text=True)

            # 설정 파일 삭제
            Path(vpn_info['config_file']).unlink(missing_ok=True)

            # VPN 서버 반납
            requests.get(
                f"{self.api_url}/release",
                params={'key': vpn_info['public_key']},
                timeout=5
            )

            # 할당 키 목록에서 제거
            self.allocated_keys.discard(vpn_info['public_key'])
            _allocated_keys.discard(vpn_info['public_key'])

            return True

        except Exception as e:
            print(f"⚠️  VPN 반납 중 오류: {str(e)[:50]}")
            return False

    def get_current_ip(self) -> str:
        """
        현재 외부 IP 주소 확인 (curl-cffi 사용)

        Returns:
            IP 주소 문자열
        """
        try:
            resp = cf_requests.get("https://api.ipify.org?format=json", timeout=5)
            return resp.json()['ip']
        except Exception as e:
            return f"Error: {str(e)[:50]}"

    def verify_connection(self, expected_ip: str = None) -> Dict:
        """
        VPN 연결 검증

        Args:
            expected_ip: 예상되는 IP 주소 (선택)

        Returns:
            검증 결과 딕셔너리
        """
        current_ip = self.get_current_ip()

        result = {
            'current_ip': current_ip,
            'is_vpn': not current_ip.startswith('Error'),
            'match': False
        }

        if expected_ip:
            result['match'] = (current_ip == expected_ip)
            result['expected_ip'] = expected_ip

        return result

    def print_status(self):
        """VPN 서버 상태 출력"""
        status = self.get_server_status()

        if not status['success']:
            print("❌ VPN 서버 상태 조회 실패")
            print(f"   오류: {status.get('error', 'Unknown')}")
            return

        print("="*60)
        print("VPN 서버 상태")
        print("="*60)
        print()

        total = status['total_available']
        servers = status['servers']

        print(f"총 사용 가능한 슬롯: {total}개")
        print()

        if servers:
            print("서버별 상세 정보:")
            for server in servers:
                ip = server['server_ip']
                slots = server['available_slots']
                location = server.get('location', 'Unknown')
                print(f"  {ip:20} | {location:5} | {slots}개 슬롯")
            print()

        if total == 0:
            print("⚠️  현재 사용 가능한 VPN 서버가 없습니다!")
        elif total < 5:
            print(f"⚠️  사용 가능한 슬롯이 {total}개뿐입니다. 주의 필요.")
        else:
            print(f"✅ {total}개 슬롯 사용 가능 - 여유 있음")


# 편의 함수들 (함수형 인터페이스)

def allocate_vpn() -> Optional[Dict]:
    """
    VPN 할당 (전역 함수)

    Returns:
        VPN 정보 딕셔너리 또는 None
    """
    manager = VPNManager()
    return manager.allocate()


def release_vpn(vpn_info: Dict) -> bool:
    """
    VPN 반납 (전역 함수)

    Args:
        vpn_info: VPN 정보 딕셔너리

    Returns:
        성공 여부
    """
    manager = VPNManager()
    return manager.release(vpn_info)


def get_current_ip() -> str:
    """
    현재 IP 확인 (전역 함수)

    Returns:
        IP 주소 문자열
    """
    manager = VPNManager()
    return manager.get_current_ip()


def get_available_servers() -> List[Dict]:
    """
    사용 가능한 서버 목록 (전역 함수)

    Returns:
        서버 목록
    """
    manager = VPNManager()
    return manager.get_available_servers()


def print_vpn_status():
    """VPN 서버 상태 출력 (전역 함수)"""
    manager = VPNManager()
    manager.print_status()


# Context Manager 지원
class VPNConnection:
    """
    VPN 연결 Context Manager

    사용 예시:
        with VPNConnection() as vpn:
            if vpn:
                print(f"연결된 IP: {vpn['server_ip']}")
                # 작업 수행...
    """

    def __init__(self, manager: VPNManager = None):
        self.manager = manager or VPNManager()
        self.vpn_info = None

    def __enter__(self):
        self.vpn_info = self.manager.allocate()
        if self.vpn_info:
            time.sleep(2)  # VPN 안정화
        return self.vpn_info

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.vpn_info:
            self.manager.release(self.vpn_info)
        return False


if __name__ == "__main__":
    # 테스트 코드
    print("VPN Manager 테스트")
    print()

    # 서버 상태 확인
    print_vpn_status()
    print()

    # Context Manager 사용 예시
    print("Context Manager 테스트:")
    with VPNConnection() as vpn:
        if vpn:
            manager = VPNManager()
            current_ip = manager.get_current_ip()
            print(f"✅ VPN 연결됨: {vpn['server_ip']}")
            print(f"   현재 IP: {current_ip}")
        else:
            print("❌ VPN 연결 실패")

    print("\n테스트 완료")

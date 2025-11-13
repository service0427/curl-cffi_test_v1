#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
안전한 테스트 프레임워크
====================

🚨 VPN 안전 규칙 (절대 위반 금지!)
========================================
이 파일은 VPN을 사용하는 유일하게 허용된 파일입니다.
단 한 번의 VPN 실수로도 전체 네트워크가 마비될 수 있습니다!

⚠️ 절대 규칙:
1. VPNConnection은 반드시 context manager (with문)로만 사용
2. DB 데이터는 VPN 연결 전에 미리 로드
3. 모든 결과는 VPN 해제 후 DB에 저장
4. 이 파일 밖에서는 절대 VPN 사용 금지!

✅ 올바른 사용법:
- 이 파일의 scenarios 리스트만 수정해서 테스트 추가
- execute_single_test() 함수의 파라미터만 변경
- VPN 관련 코드는 절대 수정하지 않음

❌ 절대 금지:
- 새로운 Python 파일에서 VPNConnection 사용
- Bash에서 wg-quick 직접 실행
- Context manager 없이 VPN 사용
- 임시 테스트 스크립트에서 VPN 사용

상세 내용: VPN_SAFETY_RULES.md 참고

테스트 시나리오:
- 정상 매칭: 핑거프린트와 쿠키가 같은 디바이스
- 크로스 테스트: 핑거프린트와 쿠키가 다른 디바이스
- 네트워크: DIRECT / VPN / SOCKS5 / VPN+SOCKS5
"""

from curl_cffi import requests as cf_requests
from curl_cffi.const import CurlSslVersion
import json
import time
import sys
from datetime import datetime
from typing import Dict, Optional, Tuple
from db.db_manager import get_db_manager
from common.vpn_manager import VPNConnection
from common.proxy_manager import ProxyManager


# ============================================================================
# 로깅 함수
# ============================================================================

def log_section(title):
    print('\n' + '=' * 100)
    print(f'  {title}')
    print('=' * 100)


def log_info(msg, indent=0):
    print('  ' * indent + f'ℹ️  {msg}')


def log_success(msg, indent=0):
    print('  ' * indent + f'✅ {msg}')


def log_warning(msg, indent=0):
    print('  ' * indent + f'⚠️  {msg}')


def log_error(msg, indent=0):
    print('  ' * indent + f'❌ {msg}')


def log_data(label, value, indent=0):
    print('  ' * indent + f'📊 {label}: {value}')


# ============================================================================
# 데이터 로더 (VPN 연결 전 실행)
# ============================================================================

def load_test_data(fingerprint_id: int, cookie_id: int) -> Optional[Tuple[Dict, Dict, Dict]]:
    """
    DB에서 테스트 데이터 로드 (VPN 연결 전에 실행!)

    Returns:
        (fingerprint, cookie_data, cookies_dict) 또는 None
    """
    try:
        db = get_db_manager()

        # 핑거프린트 로드
        fp = db.get_fingerprint(fingerprint_id)
        if not fp:
            log_error(f'핑거프린트 ID {fingerprint_id} 없음')
            return None

        # 쿠키 로드
        cookie_data = db.get_cookies(cookie_id)
        if not cookie_data:
            log_error(f'쿠키 ID {cookie_id} 없음')
            return None

        cookies_list = json.loads(cookie_data['cookies_json'])
        cookies_dict = {c['name']: c['value'] for c in cookies_list}

        return (fp, cookie_data, cookies_dict)

    except Exception as e:
        log_error(f'데이터 로드 실패: {e}')
        return None


# ============================================================================
# 테스트 실행기
# ============================================================================

def execute_single_test(
    scenario_name: str,
    test_type: str,
    fingerprint_id: int,
    cookie_id: int,
    use_vpn: bool = False,
    use_socks5: bool = False
) -> Dict:
    """
    단일 테스트 실행 (안전한 방식)

    Args:
        scenario_name: 시나리오 이름
        test_type: 'DIRECT' / 'VPN' / 'PROXY' / 'VPN_PROXY'
        fingerprint_id: 핑거프린트 ID
        cookie_id: 쿠키 ID
        use_vpn: VPN 사용 여부
        use_socks5: SOCKS5 사용 여부

    Returns:
        테스트 결과 딕셔너리
    """

    result = {
        'scenario_name': scenario_name,
        'test_type': test_type,
        'fingerprint_id': fingerprint_id,
        'cookie_id': cookie_id,
        'started_at': datetime.now(),
        'success': False,
        'error': None,
        'blocked': False,
        'has_products': False,
        'product_count': 0,
        'response_size': 0,
        'response_time_ms': 0,
        'status_code': None,
        'source_ip': None,
        'vpn_server_ip': None,
        'proxy_server': None,
        'response_html': None
    }

    log_info(f'[{scenario_name}] 시작...')

    # ========================================================================
    # 1단계: VPN 연결 전에 DB에서 모든 데이터 로드
    # ========================================================================

    log_info('DB에서 데이터 로드 중...', indent=1)

    test_data = load_test_data(fingerprint_id, cookie_id)
    if not test_data:
        result['error'] = 'DataLoadFailed'
        return result

    fp, cookie_data, cookies_dict = test_data

    log_success(f'핑거프린트: {fp["device_name"]} (ID: {fingerprint_id})', indent=1)
    log_success(f'쿠키: {cookie_data["cookie_count"]}개 (ID: {cookie_id}, 사용: {cookie_data["usage_count"]}회)', indent=1)

    # TLS 설정 준비
    JA3 = fp['ja3_text']
    AKAMAI = fp['akamai_text']
    UA = fp['user_agent']

    if fp['signature_algorithms'] and fp['signature_algorithms'].strip():
        try:
            sig_algos = json.loads(fp['signature_algorithms'])
        except:
            sig_algos = None
    else:
        sig_algos = None

    if not sig_algos:
        sig_algos = [
            'ecdsa_secp256r1_sha256', 'rsa_pss_rsae_sha256', 'rsa_pkcs1_sha256',
            'ecdsa_secp384r1_sha384', 'ecdsa_sha1', 'rsa_pss_rsae_sha384',
            'rsa_pkcs1_sha384', 'rsa_pss_rsae_sha512', 'rsa_pkcs1_sha512', 'rsa_pkcs1_sha1'
        ]

    EXTRA_FP = {
        'tls_signature_algorithms': sig_algos,
        'tls_min_version': CurlSslVersion.TLSv1_2,
    }

    HEADERS = {
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Sec-Fetch-Site': 'same-origin',
        'Sec-Fetch-Dest': 'document',
        'Accept-Language': 'ko-KR,ko;q=0.9',
        'Sec-Fetch-Mode': 'navigate',
        'User-Agent': UA,
        'Referer': 'https://www.coupang.com/',
        'Accept-Encoding': 'gzip, deflate, br',
    }

    search_url = 'https://www.coupang.com/np/search?q=노트북'

    # SOCKS5 프록시 준비 (VPN 전에!)
    proxy_info = None
    if use_socks5:
        log_info('SOCKS5 프록시 조회 중...', indent=1)
        proxy_mgr = ProxyManager()
        proxy_info = proxy_mgr.get_random_proxy()
        if proxy_info:
            result['proxy_server'] = proxy_info['proxy']
            log_success(f'SOCKS5: {proxy_info["proxy"]} (IP: {proxy_info["external_ip"]})', indent=1)
        else:
            log_warning('SOCKS5 프록시 없음', indent=1)

    # ========================================================================
    # 2단계: 네트워크 설정 및 요청 (VPN context manager 사용)
    # ========================================================================

    try:
        # VPN 사용 시 context manager로 안전하게 처리
        if use_vpn:
            log_info('VPN 연결 시작...', indent=1)

            with VPNConnection() as vpn:
                if not vpn:
                    log_error('VPN 연결 실패', indent=1)
                    result['error'] = 'VPNConnectionFailed'
                    return result

                result['vpn_server_ip'] = vpn['server_ip']
                log_success(f'VPN 연결 완료: {vpn["server_ip"]}', indent=1)

                # VPN 연결 후 IP 확인
                try:
                    import requests as std_requests
                    resp = std_requests.get('https://ifconfig.me', timeout=5)
                    result['source_ip'] = resp.text.strip()
                    log_data('현재 IP', result['source_ip'], indent=1)
                except:
                    pass

                # 요청 실행
                log_info('요청 전송 중...', indent=1)
                start_time = time.time()

                proxies = None
                if use_socks5 and proxy_info:
                    proxies = {
                        'http': f"socks5://{proxy_info['proxy']}",
                        'https': f"socks5://{proxy_info['proxy']}"
                    }

                response = cf_requests.get(
                    search_url,
                    headers=HEADERS,
                    cookies=cookies_dict,
                    ja3=JA3,
                    akamai=AKAMAI,
                    extra_fp=EXTRA_FP,
                    proxies=proxies,
                    timeout=30
                )

                elapsed_ms = int((time.time() - start_time) * 1000)

                # 응답 처리
                result['success'] = True
                result['status_code'] = response.status_code
                result['response_time_ms'] = elapsed_ms
                result['response_size'] = len(response.text)
                result['response_html'] = response.text

                # 봇 차단 확인
                if result['response_size'] < 2000:
                    result['blocked'] = True
                else:
                    result['has_products'] = 'id="product-list"' in response.text or 'id="productList"' in response.text
                    if result['has_products']:
                        result['product_count'] = response.text.count('/vp/products/')

                log_success(f'Status: {result["status_code"]}, Size: {result["response_size"]:,} bytes, 소요: {elapsed_ms}ms', indent=1)

                if result['blocked']:
                    log_error('봇 차단 감지', indent=1)
                elif result['has_products']:
                    log_success(f'🎉 제품 검색 성공! ({result["product_count"]}개 링크)', indent=1)
                else:
                    log_warning('부분 성공 (제품 없음)', indent=1)

            # with 블록 종료 - VPN 자동 해제됨
            log_info('VPN 연결 해제 완료', indent=1)

        else:
            # VPN 없이 직접 연결
            log_info('직접 연결 (VPN 없음)', indent=1)

            # 현재 IP 확인
            try:
                import requests as std_requests
                resp = std_requests.get('https://ifconfig.me', timeout=5)
                result['source_ip'] = resp.text.strip()
                log_data('현재 IP', result['source_ip'], indent=1)
            except:
                pass

            # 요청 실행
            log_info('요청 전송 중...', indent=1)
            start_time = time.time()

            proxies = None
            if use_socks5 and proxy_info:
                proxies = {
                    'http': f"socks5://{proxy_info['proxy']}",
                    'https': f"socks5://{proxy_info['proxy']}"
                }

            response = cf_requests.get(
                search_url,
                headers=HEADERS,
                cookies=cookies_dict,
                ja3=JA3,
                akamai=AKAMAI,
                extra_fp=EXTRA_FP,
                proxies=proxies,
                timeout=30
            )

            elapsed_ms = int((time.time() - start_time) * 1000)

            # 응답 처리
            result['success'] = True
            result['status_code'] = response.status_code
            result['response_time_ms'] = elapsed_ms
            result['response_size'] = len(response.text)
            result['response_html'] = response.text

            # 봇 차단 확인
            if result['response_size'] < 2000:
                result['blocked'] = True
            else:
                result['has_products'] = 'id="product-list"' in response.text or 'id="productList"' in response.text
                if result['has_products']:
                    result['product_count'] = response.text.count('/vp/products/')

            log_success(f'Status: {result["status_code"]}, Size: {result["response_size"]:,} bytes, 소요: {elapsed_ms}ms', indent=1)

            if result['blocked']:
                log_error('봇 차단 감지', indent=1)
            elif result['has_products']:
                log_success(f'🎉 제품 검색 성공! ({result["product_count"]}개 링크)', indent=1)
            else:
                log_warning('부분 성공 (제품 없음)', indent=1)

    except Exception as e:
        result['error'] = f'{type(e).__name__}: {str(e)[:200]}'
        log_error(result['error'], indent=1)

    return result


# ============================================================================
# DB 저장 함수 (VPN 해제 후 실행)
# ============================================================================

def save_result_to_db(result: Dict) -> Optional[int]:
    """
    테스트 결과를 DB에 저장

    Returns:
        test_execution ID 또는 None
    """
    try:
        db = get_db_manager()

        data = {
            'fingerprint_id': result['fingerprint_id'],
            'cookie_id': result['cookie_id'],
            'test_type': result['test_type'],
            'test_name': result['scenario_name'],
            'executed_at': result['started_at'],
            'source_ip': result['source_ip'],
            'vpn_server_ip': result['vpn_server_ip'],
            'proxy_server': result['proxy_server'],
            'url': 'https://www.coupang.com/np/search?q=노트북',
            'method': 'GET',
            'headers_json': None,
            'ja3_used': None,
            'akamai_used': None,
            'extra_fp_json': None,
            'status_code': result['status_code'],
            'response_time_ms': result['response_time_ms'],
            'response_size_bytes': result['response_size'],
            'response_headers_json': None,
            'success': result['success'] and not result['blocked'],
            'blocked': result['blocked'],
            'has_product_list': result['has_products'],
            'product_count': result['product_count'],
            'response_html': result['response_html'],
            'response_preview': result['response_html'][:500] if result['response_html'] else None,
            'error_message': result['error'],
            'error_type': result['error'].split(':')[0] if result['error'] else None,
            'script_file': 'safe_test_framework.py',
            'notes': None
        }

        test_id = db.insert_test_execution(data)
        return test_id

    except Exception as e:
        log_error(f'DB 저장 실패: {e}')
        return None


# ============================================================================
# 메인 테스트 실행
# ============================================================================

def run_tests():
    """종합 테스트 실행"""

    log_section('안전한 테스트 프레임워크')
    log_info(f'시작 시간: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}')

    # DB에서 사용 가능한 핑거프린트/쿠키 확인
    print()
    log_info('사용 가능한 핑거프린트/쿠키 확인 중...')

    db = get_db_manager()
    fingerprints = db.list_fingerprints(limit=10)

    log_success(f'핑거프린트: {len(fingerprints)}개 발견')

    # 아이폰과 갤럭시 찾기
    iphone_fp = next((fp for fp in fingerprints if 'iPhone' in fp['device_name']), None)
    galaxy_fp = next((fp for fp in fingerprints if 'Galaxy' in fp['device_name'] or 'Samsung' in fp['device_name']), None)

    if iphone_fp:
        log_data('아이폰', f"{iphone_fp['device_name']} (ID: {iphone_fp['id']})", indent=1)

    if galaxy_fp:
        log_data('갤럭시', f"{galaxy_fp['device_name']} (ID: {galaxy_fp['id']})", indent=1)

    # 쿠키 찾기
    with db.get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute('''
                SELECT c.*, f.device_name
                FROM cookies c
                JOIN fingerprints f ON c.fingerprint_id = f.id
                WHERE c.is_valid = TRUE AND c.usage_count < 7
                ORDER BY c.collected_at DESC
                LIMIT 10
            ''')
            cookies = cursor.fetchall()

    log_success(f'유효한 쿠키: {len(cookies)}개 발견')

    iphone_cookie = next((c for c in cookies if 'iPhone' in c['device_name']), None)
    galaxy_cookie = next((c for c in cookies if 'Galaxy' in c['device_name'] or 'Samsung' in c['device_name']), None)

    if iphone_cookie:
        log_data('아이폰 쿠키', f"ID: {iphone_cookie['id']} (사용: {iphone_cookie['usage_count']}회)", indent=1)

    if galaxy_cookie:
        log_data('갤럭시 쿠키', f"ID: {galaxy_cookie['id']} (사용: {galaxy_cookie['usage_count']}회)", indent=1)

    # 테스트 시나리오 정의
    scenarios = []

    # 쿠키 믹싱 테스트 추가 - VPN으로 IP 바꿔서 동일 조건 테스트
    # 핑거프린트 18, 쿠키 20 (신규)
    # 핑거프린트 15, 쿠키 14 (기존)
    scenarios.extend([
        # 베이스라인
        ('쿠키믹싱-VPN: 베이스라인 1 - 신규 전체', 'VPN', 18, 20, True, False),

        # 핵심 테스트: 신규 필수만
        ('쿠키믹싱-VPN: 테스트 1 - 신규 FP + 신규 필수만', 'VPN', 18, 20, True, False),

        # 핵심 테스트: 기존 FP + 신규 필수만 (쿠키 값 이식)
        ('쿠키믹싱-VPN: 테스트 6 - 기존 FP + 신규 필수만', 'VPN', 15, 20, True, False),

        # 추가: 직접 연결과 비교
        ('쿠키믹싱-직접: 신규 FP + 신규 필수만', 'DIRECT', 18, 20, False, False),
        ('쿠키믹싱-직접: 기존 FP + 신규 필수만', 'DIRECT', 15, 20, False, False),
    ])

    # 기존 시나리오 (사용 가능한 경우만)
    if iphone_fp and iphone_cookie:
        scenarios.extend([
            ('시나리오 1: VPN + 아이폰 FP + 아이폰 쿠키', 'VPN', iphone_fp['id'], iphone_cookie['id'], True, False),
            ('시나리오 2: SOCKS5 + 아이폰 FP + 아이폰 쿠키', 'PROXY', iphone_fp['id'], iphone_cookie['id'], False, True),
            ('시나리오 3: VPN+SOCKS5 + 아이폰 FP + 아이폰 쿠키', 'VPN_PROXY', iphone_fp['id'], iphone_cookie['id'], True, True),
            ('시나리오 4: 직접 연결 + 아이폰 FP + 아이폰 쿠키', 'DIRECT', iphone_fp['id'], iphone_cookie['id'], False, False),
        ])

    if galaxy_fp and galaxy_cookie and iphone_fp and iphone_cookie:
        scenarios.extend([
            ('시나리오 5: VPN + 갤럭시 FP + 아이폰 쿠키 (크로스)', 'VPN', galaxy_fp['id'], iphone_cookie['id'], True, False),
            ('시나리오 6: VPN + 아이폰 FP + 갤럭시 쿠키 (크로스)', 'VPN', iphone_fp['id'], galaxy_cookie['id'], True, False),
        ])

    if not scenarios:
        log_error('테스트 가능한 핑거프린트/쿠키 조합이 없습니다.')
        return

    # 테스트 실행
    results = []
    interval = 5  # 5초 간격

    for i, (name, test_type, fp_id, cookie_id, use_vpn, use_socks5) in enumerate(scenarios, 1):
        print()
        log_section(f'테스트 {i}/{len(scenarios)}: {name}')

        # 테스트 실행
        result = execute_single_test(name, test_type, fp_id, cookie_id, use_vpn, use_socks5)
        results.append(result)

        # DB 저장 (VPN 해제 후!)
        log_info('DB 저장 중...', indent=1)
        test_id = save_result_to_db(result)
        if test_id:
            log_success(f'DB 저장 완료 (test_execution ID: {test_id})', indent=1)
        else:
            log_warning('DB 저장 실패', indent=1)

        # 다음 테스트 전 대기
        if i < len(scenarios):
            log_info(f'{interval}초 대기 중...', indent=1)
            time.sleep(interval)

    # 결과 요약
    print()
    log_section('테스트 결과 요약')

    total = len(results)
    successful = sum(1 for r in results if r['success'] and r['has_products'])
    blocked = sum(1 for r in results if r['blocked'])
    errors = sum(1 for r in results if r['error'])

    log_data('총 테스트', f'{total}개')
    log_data('완전 성공', f'{successful}/{total} ({successful/total*100:.1f}%)')
    log_data('봇 차단', f'{blocked}/{total} ({blocked/total*100:.1f}%)')
    log_data('에러', f'{errors}/{total} ({errors/total*100:.1f}%)')

    print()
    log_info('각 시나리오 결과:')

    for i, r in enumerate(results, 1):
        status_icon = '✅' if r['success'] and r['has_products'] else '❌' if r['blocked'] or r['error'] else '⚠️'
        status_text = '완전 성공' if r['success'] and r['has_products'] else '봇 차단' if r['blocked'] else '에러' if r['error'] else '부분 성공'

        log_info(f'{status_icon} #{i}: {r["scenario_name"]}', indent=1)
        log_info(f'→ {status_text}', indent=2)

        if r['success']:
            log_info(f'→ Size: {r["response_size"]:,} bytes, 제품: {r["product_count"]}개', indent=2)
        elif r['error']:
            log_info(f'→ {r["error"][:80]}', indent=2)

    # DB daily summary 업데이트
    print()
    log_info('일일 요약 업데이트 중...')
    db.update_daily_summary()
    log_success('일일 요약 업데이트 완료')

    print()
    log_section('테스트 완료')
    log_info(f'종료 시간: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}')
    log_info('모든 결과가 DB에 저장되었습니다.')
    log_info('분석: python3 analyze_test_history.py')


if __name__ == '__main__':
    try:
        run_tests()
    except KeyboardInterrupt:
        print('\n\n중단됨')
        sys.exit(1)
    except Exception as e:
        print(f'\n\n❌ 예상치 못한 오류: {e}')
        import traceback
        traceback.print_exc()
        sys.exit(1)

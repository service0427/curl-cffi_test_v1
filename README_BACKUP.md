# curl-cffi 테스트 참고 자료

**백업 날짜**: 2025-11-12
**목적**: 다른 기기에서 curl-cffi 구현 시 필수 설정값 참고

---

## 📁 백업 내용

### 핵심 문서
- **[README.md](README.md)** - 빠른 시작
- **[CURL_CFFI_GUIDE.md](CURL_CFFI_GUIDE.md)** - curl-cffi 매칭 가이드 ⭐ 가장 중요!
- **[VPN_SAFETY_RULES.md](VPN_SAFETY_RULES.md)** - VPN 안전 규칙
- **[FRAMEWORK.md](FRAMEWORK.md)** - 전체 프레임워크
- **[CLAUDE.md](CLAUDE.md)** - 프로젝트 개요
- **[SUMMARY.md](SUMMARY.md)** - 프로젝트 정리 요약

### 샘플 코드 (examples/)
- **[safe_test_framework.py](examples/safe_test_framework.py)** - VPN + curl-cffi 전체 예제
- **[check_critical_rules.py](examples/check_critical_rules.py)** - DB 규칙 확인
- **[db/policy_loader.py](examples/db/policy_loader.py)** - 정책 로더
- **[db/db_manager.py](examples/db/db_manager.py)** - DB 연결 설정
- **[common/vpn_manager.py](examples/common/vpn_manager.py)** - VPN 관리
- **[common/proxy_manager.py](examples/common/proxy_manager.py)** - Proxy 관리

### 참고 문서 (docs/)
- [PROJECT_STATUS.md](docs/PROJECT_STATUS.md) - 프로젝트 현황
- [DB_WORKFLOW.md](docs/DB_WORKFLOW.md) - DB 워크플로우
- [CHANGELOG.md](docs/CHANGELOG.md) - 변경 이력

---

## 🎯 핵심 설정값 (curl-cffi)

### 쿠키 설정 (가장 중요!)

```python
# ✅ 올바른 방법 (dict 방식)
cookies_dict = {c['name']: c['value'] for c in cookies_list}

response = cf_requests.get(
    url,
    headers=HEADERS,
    cookies=cookies_dict,  # dict로 직접 전달!
    ja3=JA3,
    akamai=AKAMAI,
    extra_fp=EXTRA_FP
)
```

```python
# ❌ 잘못된 방법 (session.cookies.set - 탐지됨!)
session = cf_requests.Session()
for cookie in cookies_list:
    session.cookies.set(cookie['name'], cookie['value'])
response = session.get(url, ...)  # 실패!
```

### TLS 설정

```python
from curl_cffi.const import CurlSslVersion

EXTRA_FP = {
    'tls_signature_algorithms': [
        'ecdsa_secp256r1_sha256',
        'rsa_pss_rsae_sha256',
        'rsa_pkcs1_sha256',
        'ecdsa_secp384r1_sha384',
        'ecdsa_sha1',
        'rsa_pss_rsae_sha384',
        'rsa_pkcs1_sha384',
        'rsa_pss_rsae_sha512',
        'rsa_pkcs1_sha512',
        'rsa_pkcs1_sha1'
    ],
    'tls_min_version': CurlSslVersion.TLSv1_2,
}
```

### 헤더 설정

```python
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
```

### VPN 사용 (필수)

```python
from common.vpn_manager import VPNConnection

# ✅ Context Manager 사용
with VPNConnection() as vpn:
    if vpn:
        response = cf_requests.get(url, cookies=cookies_dict, ...)
# VPN 자동 해제
```

---

## 🚨 중요 규칙

### 1. 쿠키
- **dict 방식 필수**: `cookies={name: value}`
- **session.cookies.set() 금지**: Akamai에 탐지됨
- **수명**: 동일 쿠키 7~10회 사용 후 블랙리스트

### 2. VPN
- **Context Manager 필수**: `with VPNConnection() as vpn:`
- **직접 wg-quick 실행 금지**: 네트워크 마비 위험
- **DB 로드 먼저**: VPN 연결 전에 모든 데이터 로드

### 3. 성공 판단
- **1.4MB 이상**: 완전 성공 (제품 목록 포함)
- **2KB 미만**: 봇 차단 (JavaScript 챌린지)
- **VPN 없이**: 첫 1회만 성공, 이후 차단

---

## 📖 사용법

### 빠른 시작
1. [CURL_CFFI_GUIDE.md](CURL_CFFI_GUIDE.md) 읽기 (필수!)
2. [safe_test_framework.py](examples/safe_test_framework.py) 참고
3. 쿠키 dict 방식 적용
4. VPN Context Manager 적용

### 주의 사항
- 이 저장소는 **참고용**입니다
- 실제 데이터, 로그, 전체 소스는 포함되지 않음
- DB 연결 정보는 샘플 코드에서 확인

---

## 🔧 DB 연결 (참고)

```python
DB_CONFIG = {
    'host': '220.121.120.83',
    'user': 'tls_user',
    'password': 'TLS_Pass_2024!@',
    'database': 'tls',
    'charset': 'utf8mb4'
}
```

---

## 📊 프로젝트 성과

- ✅ curl-cffi 쿠키 dict 방식 검증 완료
- ✅ VPN Context Manager 안전 규칙 확립
- ✅ DB 기반 정책 관리 시스템 구축
- ✅ 안정적인 테스트 프레임워크 완성
- ✅ 쿠키 7~10회 수명 확인

---

**이 자료는 다른 기기에서 curl-cffi 구현 시 필수 설정값을 참고하기 위한 것입니다.**

**가장 중요한 것**: 쿠키를 dict로 전달하는 방식! (`cookies={name: value}`)

# curl-cffi 성공 가이드

## 🎯 핵심 발견 사항 (2025-11-11 검증 완료)

### ✅ 성공하는 방법

#### 1. 쿠키를 dict로 직접 전달
```python
# ❌ 실패하는 방법 (session.cookies.set 사용)
session = cf_requests.Session()
for cookie in cookies_list:
    session.cookies.set(
        cookie['name'],
        cookie['value'],
        domain=cookie.get('domain', '.coupang.com'),
        path=cookie.get('path', '/')
    )
response = session.get(url, headers=headers, ja3=ja3, akamai=akamai, extra_fp=extra_fp)

# ✅ 성공하는 방법 (cookies 파라미터로 dict 직접 전달)
cookies_dict = {c['name']: c['value'] for c in cookies_list}
response = cf_requests.get(
    url,
    headers=headers,
    cookies=cookies_dict,  # dict로 직접 전달!
    ja3=ja3,
    akamai=akamai,
    extra_fp=extra_fp,
    timeout=30
)
```

**이유:** `session.cookies.set()`은 curl-cffi 내부 처리 문제로 Coupang Bot Manager에 탐지됨

#### 2. VPN 필수 사용
```python
from common.vpn_manager import VPNConnection

with VPNConnection() as vpn:
    if vpn:
        print(f"VPN IP: {vpn['server_ip']}")

        # 쿠키 dict 변환
        cookies_dict = {c['name']: c['value'] for c in cookies_list}

        # 요청
        response = cf_requests.get(
            'https://www.coupang.com/np/search?q=노트북',
            headers=headers,
            cookies=cookies_dict,
            ja3=ja3,
            akamai=akamai,
            extra_fp=extra_fp,
            timeout=30
        )
```

**이유:** 서버 IP (221.154.194.11)가 반복 테스트로 블랙리스트에 등록됨

### 📊 검증 결과

**VPN 없이 (서버 직접 IP):**
```
테스트 1: ✅ 성공 (1.4MB, 120개 링크)
테스트 2~10: ❌ 차단 (1.2KB)
성공률: 10%
```

**VPN 사용 (IP 변경):**
```
테스트 1~7: ✅ 성공 (1.4~1.5MB, 120개 링크)
테스트 8~10: ❌ 차단 (쿠키 블랙리스트 등록)
성공률: 70%
```

### 🔄 쿠키 수명

- **동일 쿠키로 약 7~10회 사용 가능**
- 이후 쿠키가 블랙리스트에 등록됨
- 신규 쿠키 수집 필요

### 📝 완전한 예제

```python
from curl_cffi import requests as cf_requests
from curl_cffi.const import CurlSslVersion
import json
from db.db_manager import get_db_manager
from common.vpn_manager import VPNConnection

# DB에서 로드
fingerprint_id = 16
cookie_id = 15

db = get_db_manager()

with db.get_connection() as conn:
    with conn.cursor() as cursor:
        cursor.execute('''
            SELECT user_agent, ja3_text, akamai_text, signature_algorithms
            FROM fingerprints
            WHERE id = %s
        ''', (fingerprint_id,))
        fp = cursor.fetchone()

        cursor.execute('''
            SELECT cookies_json
            FROM cookies
            WHERE id = %s
        ''', (cookie_id,))
        cookie_data = cursor.fetchone()

cookies_list = json.loads(cookie_data['cookies_json'])

# ✅ 핵심: 쿠키를 dict로 변환
cookies_dict = {c['name']: c['value'] for c in cookies_list}

# TLS 설정
JA3 = fp['ja3_text']
AKAMAI = fp['akamai_text']
UA = fp['user_agent']

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

# ✅ VPN 사용
with VPNConnection() as vpn:
    if vpn:
        print(f"VPN IP: {vpn['server_ip']}")

        # ✅ 쿠키를 dict로 직접 전달
        response = cf_requests.get(
            'https://www.coupang.com/np/search?q=노트북',
            headers=HEADERS,
            cookies=cookies_dict,  # ✅ 핵심!
            ja3=JA3,
            akamai=AKAMAI,
            extra_fp=EXTRA_FP,
            timeout=30
        )

        print(f"Status: {response.status_code}")
        print(f"Size: {len(response.text):,} bytes")

        if len(response.text) > 100000:
            print("✅ 성공!")
```

## 🚨 절대 금지 사항

### ❌ session.cookies.set() 사용
```python
# 이 방식은 작동하지 않음!
session = cf_requests.Session()
session.cookies.set('name', 'value', domain='.coupang.com', path='/')
```

### ❌ VPN 없이 반복 테스트
```python
# 서버 IP로 직접 테스트하면 첫 1회만 성공하고 이후 차단됨
response = cf_requests.get(url, cookies=cookies_dict, ...)
```

## 📈 테스트 전략

### 권장 방식
1. **VPN 연결**
2. **쿠키 dict로 변환**
3. **7~10회 테스트**
4. **신규 쿠키 수집**
5. **반복**

### 최적 간격
- 연속 테스트: 2~3초 간격
- 쿠키당 수명: 7~10회
- 신규 쿠키 수집 주기: 7회 사용 후

## 🔍 디버깅 가이드

### 성공 여부 확인
```python
if len(response.text) > 100000:
    # 성공 (1MB 이상)
    has_products = 'id="product-list"' in response.text
    product_links = response.text.count('/vp/products/')
    print(f"제품 링크: {product_links}개")
elif len(response.text) < 2000:
    # 봇 차단 (1~2KB JavaScript 챌린지)
    print("봇 차단")
else:
    # 중간 크기 응답
    print("부분 성공")
```

### IP 확인
```python
# VPN 사용 전
import requests
original_ip = requests.get('https://ifconfig.me').text
print(f"원본 IP: {original_ip}")

# VPN 사용 후
with VPNConnection() as vpn:
    if vpn:
        print(f"VPN IP: {vpn['server_ip']}")
```

## 🔗 관련 파일

- **성공 스크립트**: `/home/tech/test/test_cookies_as_dict.py`
- **반복 테스트**: `/home/tech/test/test_cookies_dict_repeat.py`
- **VPN 관리**: `/home/tech/test/common/vpn_manager.py`
- **DB 정책**: `project_policies` 테이블

## 📅 검증 일자

- **2025-11-11 10:19 KST**: 쿠키 dict 방식 발견
- **2025-11-11 10:23 KST**: VPN 없이 1/10 성공 확인
- **2025-11-11 10:24 KST**: VPN 사용 시 5/5 성공 확인
- **2025-11-11 10:26 KST**: VPN 사용 시 7/10 성공 확인 (쿠키 수명)

## ✅ 체크리스트

테스트 전 확인 사항:
- [ ] 쿠키를 dict로 변환했는가?
- [ ] VPN을 연결했는가?
- [ ] cookies 파라미터로 전달하는가?
- [ ] session.cookies.set()을 사용하지 않았는가?
- [ ] 쿠키 사용 횟수가 7회 이내인가?

# TLS 핑거프린트 테스트 프레임워크 v3.0

**최종 업데이트**: 2025-11-12
**프로젝트 목표**: 실기기 TLS 핑거프린트를 curl-cffi에 완벽하게 매칭하여 Akamai Bot Manager 우회

---

## 🎯 프로젝트 개요

### 목표
실기기(iPhone, Galaxy)에서 수집한 TLS 핑거프린트와 쿠키를 curl-cffi에 커스텀 방식으로 매칭하여 쿠팡 봇 탐지를 우회하는 것

### 현재 상태
- ✅ 안정적인 테스트 프레임워크 완성
- ✅ DB 기반 정책 관리 시스템 구축
- ✅ VPN 안전 사용 규칙 확립
- ✅ curl-cffi 쿠키 설정 방법 검증 완료
- ⏳ 세부 테스트 진행 중 (nodriver 전환 예정)

### 핵심 원칙
1. **DB 중심 시스템**: 모든 정책과 테스트 결과는 DB에 저장
2. **VPN 안전 규칙**: VPN은 safe_test_framework.py에서만 사용
3. **쿠키 dict 방식**: `cookies={name: value}` 형태로 전달 필수
4. **실기기 우선**: BrowserStack 대신 nodriver로 전환 예정

---

## 📁 프로젝트 구조

```
/home/tech/test/
├── CLAUDE.md                       # 프로젝트 진입점
├── FRAMEWORK.md                    # 이 문서 (핵심 가이드)
├── README.md                       # 빠른 시작
├── check_critical_rules.py         # ⚠️ 작업 시작 전 필수 실행!
│
├── db/                             # DB 시스템
│   ├── db_manager.py              # DB CRUD
│   ├── policy_loader.py           # 정책 로더
│   └── init_db.py                 # DB 초기화
│
├── common/                         # 공통 모듈
│   ├── vpn_manager.py             # VPN 관리 (직접 사용 금지!)
│   └── proxy_manager.py           # Proxy 관리
│
├── safe_test_framework.py          # ⭐ VPN 사용 유일 허용 파일
├── collect_and_save_fingerprint.py # 핑거프린트 수집
├── analyze_test_history.py         # 결과 분석
│
├── VPN_SAFETY_RULES.md             # VPN 안전 규칙
├── CURL_CFFI_GUIDE.md              # curl-cffi 가이드
├── DB_WORKFLOW.md                  # DB 워크플로우
└── archive/                        # 아카이브
```

---

## 🗄️ DB 구조

**MariaDB 11.8.3** @ 220.121.120.83

### 핵심 테이블

#### 1. project_policies (정책 저장) ⭐
- 쿠키 사용 제한, VPN 규칙, 필수 쿠키 등 모든 정책
- 38개 정책 저장 (12개 카테고리)
- `check_critical_rules.py`로 확인

#### 2. fingerprints (TLS 핑거프린트)
- JA3, JA4, Akamai 해시
- User-Agent, 시그니처 알고리즘
- HTTP/2 설정

#### 3. cookies (쿠키 세트)
- 쿠키 JSON 데이터
- 사용 횟수 자동 추적 (7-10회 제한)
- has_cto_bundle 플래그

#### 4. test_executions (테스트 결과)
- 요청/응답 정보
- 성공/실패/차단 여부
- 전체 HTML 저장

#### 5. daily_summary (일일 요약)
- 날짜별 통계 자동 집계

---

## 🚀 워크플로우

### 1. 작업 시작 시 (필수!)

```bash
# 중요 규칙 확인
python3 check_critical_rules.py
```

**출력 내용**:
- 🚨 VPN 안전 규칙
- ✅ curl-cffi 필수 규칙
- 🍪 쿠키 규칙
- 🏗️ 인프라 규칙

### 2. 핑거프린트 수집

```bash
python3 collect_and_save_fingerprint.py
```

**자동 수행**:
- 실기기에서 TLS 핑거프린트 수집
- 쿠키 수집
- DB 저장 (fingerprints, cookies)
- ID 반환

### 3. 테스트 실행

```bash
# 안전한 테스트 프레임워크 사용 (VPN 포함)
python3 safe_test_framework.py
```

**자동 수행**:
- DB에서 핑거프린트/쿠키 로드
- VPN 연결 (Context Manager 사용)
- curl-cffi 요청 (쿠키 dict 방식)
- 결과 DB 저장
- VPN 자동 해제

### 4. 결과 분석

```bash
python3 analyze_test_history.py
```

**제공 정보**:
- 전체 통계 (성공률, 차단율)
- 최근 테스트 목록
- 디바이스별 성공률
- 쿠키 사용 경고 (7회 이상)

---

## 🚨 중요 규칙

### VPN 안전 규칙 (최우선!)

#### ✅ 올바른 사용법
```python
# safe_test_framework.py 파일 내에서만
from common.vpn_manager import VPNConnection

with VPNConnection() as vpn:
    if vpn:
        # VPN 연결 상태에서 작업
        response = cf_requests.get(url, ...)
# with 블록 종료 시 VPN 자동 해제
```

#### ❌ 절대 금지
- 임시 스크립트에서 VPN 사용
- Bash에서 `wg-quick` 직접 실행
- Context Manager 없이 VPN 사용
- DB 조회를 VPN 연결 중에 실행

**위반 시**: 전체 네트워크 마비 위험!

### curl-cffi 쿠키 설정 규칙

#### ✅ 올바른 방법 (dict 방식)
```python
# 쿠키를 dict로 변환
cookies_dict = {c['name']: c['value'] for c in cookies_list}

# cookies 파라미터로 전달
response = cf_requests.get(
    url,
    headers=HEADERS,
    cookies=cookies_dict,  # ✅ dict로 전달!
    ja3=JA3,
    akamai=AKAMAI,
    extra_fp=EXTRA_FP
)
```

#### ❌ 잘못된 방법 (session.cookies.set)
```python
# 이 방식은 Akamai에 탐지됨!
session = cf_requests.Session()
for cookie in cookies_list:
    session.cookies.set(
        cookie['name'],
        cookie['value'],
        domain=cookie.get('domain', '.coupang.com'),
        path=cookie.get('path', '/')
    )
response = session.get(url, ...)  # ❌ 실패
```

### 쿠키 수명 규칙

- **동일 쿠키로 7~10회 사용 가능**
- 이후 블랙리스트 등록
- DB가 자동으로 usage_count 추적
- 7회 이상 사용 시 경고 표시

---

## 🔧 핵심 파일 설명

### 1. check_critical_rules.py
**목적**: DB에서 중요 규칙을 로드하여 출력
**사용 시기**: 모든 작업 시작 전 필수 실행
**출력**: VPN 규칙, curl-cffi 규칙, 쿠키 규칙, 인프라 규칙

### 2. safe_test_framework.py
**목적**: VPN을 안전하게 사용하는 유일한 파일
**특징**:
- Context Manager로 VPN 자동 관리
- DB 데이터는 VPN 연결 전에 로드
- 쿠키 dict 방식 사용
- 결과 자동 DB 저장

### 3. db/policy_loader.py
**목적**: DB에서 정책을 동적으로 로드
**사용법**:
```python
from db.policy_loader import get_policy_loader

loader = get_policy_loader()
vpn_api_url = loader.get_vpn_api_url()
cookie_limit = loader.get('cookie_lifespan')
```

### 4. db/db_manager.py
**목적**: DB CRUD 작업 간소화
**기능**:
- 핑거프린트 저장/조회
- 쿠키 저장/조회/사용 횟수 증가
- 테스트 결과 저장
- 일일 요약 업데이트

### 5. common/vpn_manager.py
**목적**: VPN 연결 관리
**주의**: 직접 사용 금지! safe_test_framework.py에서만 사용

---

## 📊 성공 기준

### 응답 크기로 판단
- **1.4MB 이상**: 완전 성공 (제품 목록 포함)
- **2KB 미만**: 봇 차단 (JavaScript 챌린지)
- **중간 크기**: 부분 성공

### 제품 검색 확인
```python
has_products = 'id="product-list"' in response.text
product_count = response.text.count('/vp/products/')
```

---

## 🔍 문제 해결

### Q: 정책이 뭐였지?
```bash
python3 check_critical_rules.py
```

### Q: 어제는 됐는데 오늘은 안 돼
```bash
# DB에서 과거 성공 케이스 비교
python3 analyze_test_history.py
```

### Q: 쿠키를 몇 번 사용했지?
```bash
# DB에서 자동 추적
python3 analyze_test_history.py | grep "쿠키 사용 경고"
```

### Q: VPN 연결 실패
1. VPN API 상태 확인: http://220.121.120.83/vpn_api
2. 이전 VPN 연결이 남아있는지 확인: `wg show`
3. 필요 시 수동 해제: `sudo wg-quick down wg0`

---

## 🎯 다음 단계: nodriver 전환

### BrowserStack → nodriver 전환 계획

#### 이유
- BrowserStack은 클라우드 기반 (네트워크 지연)
- nodriver는 로컬에서 실제 Chrome/Chromium 제어
- 더 정확한 핑거프린트 수집 가능

#### 준비 사항
1. nodriver 설치
2. 로컬 Chrome/Chromium 설정
3. 핑거프린트 수집 스크립트 수정
4. 기존 BrowserStack 코드 제거

#### 주의 사항
- BrowserStack 관련 파일은 archive로 이동 (완전 삭제 금지)
- DB 테이블 구조는 유지
- 기존 핑거프린트 데이터는 보존

---

## 📖 관련 문서

### 필수 문서
1. **[CLAUDE.md](CLAUDE.md)** - 프로젝트 진입점
2. **[check_critical_rules.py](check_critical_rules.py)** - 중요 규칙 확인
3. **[VPN_SAFETY_RULES.md](VPN_SAFETY_RULES.md)** - VPN 안전 규칙 상세
4. **[CURL_CFFI_GUIDE.md](CURL_CFFI_GUIDE.md)** - curl-cffi 가이드

### 참고 문서
- **[DB_WORKFLOW.md](DB_WORKFLOW.md)** - DB 워크플로우
- **[NETWORK_INFO.md](NETWORK_INFO.md)** - 네트워크 정보
- **[README.md](README.md)** - 빠른 시작

---

## 🔐 시스템 정보

### DB 연결
```python
DB_CONFIG = {
    'host': '220.121.120.83',
    'user': 'tls_user',
    'password': 'TLS_Pass_2024!@',
    'database': 'tls',
    'charset': 'utf8mb4'
}
```

### VPN API
```
http://220.121.120.83/vpn_api
```

### BrowserStack (사용 중단 예정)
```bash
Username: bsuser_wHW2oU
Access Key: fuymXXoQNhshiN5BsZhp
```

---

## ✅ 작업 체크리스트

### 테스트 실행 전
- [ ] `check_critical_rules.py` 실행하여 규칙 확인
- [ ] 쿠키 사용 횟수 확인 (7회 미만인지)
- [ ] VPN API 상태 확인
- [ ] 이전 VPN 연결 해제 확인

### 테스트 실행 시
- [ ] safe_test_framework.py 사용
- [ ] 쿠키 dict 방식 사용
- [ ] VPN Context Manager 사용
- [ ] DB에 결과 자동 저장 확인

### 테스트 실행 후
- [ ] 결과 분석 (analyze_test_history.py)
- [ ] 쿠키 사용 횟수 확인
- [ ] 성공률 확인
- [ ] 필요 시 새 쿠키 수집

---

## 🎉 프레임워크 특징

### 안정성
- VPN 자동 관리로 네트워크 마비 방지
- DB 중심 설계로 데이터 손실 방지
- Context Manager로 리소스 자동 해제

### 추적성
- 모든 테스트 결과 DB 저장
- 쿠키 사용 횟수 자동 추적
- 일일 요약 자동 생성

### 확장성
- 정책 변경 시 DB만 업데이트
- 새로운 디바이스 추가 용이
- 테스트 시나리오 쉽게 추가

### 안전성
- VPN은 단일 파일에서만 사용
- 중요 규칙 DB 저장으로 일관성 유지
- 파일 삭제 금지 정책으로 데이터 보존

---

**⚠️ 이 프레임워크는 실기기 핑거프린트를 curl-cffi에 매칭하는 안정적인 환경을 제공합니다.**

**⚠️ 모든 작업 시작 전 반드시 `python3 check_critical_rules.py` 실행!**

**⚠️ nodriver 전환 후 BrowserStack 관련 코드는 archive로 이동 예정!**

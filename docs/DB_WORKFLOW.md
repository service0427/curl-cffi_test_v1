# TLS 테스트 추적 시스템 - DB 워크플로우

## 개요

이 시스템은 **모든 TLS 핑거프린트 수집, 쿠키, curl-cffi 테스트 결과를 DB에 저장**하여 완전한 히스토리 추적을 가능하게 합니다.

**핵심 목적**:
- ✅ 과거 테스트 히스토리 유지
- ✅ 성공/실패 패턴 분석
- ✅ 쿠키 사용 횟수 추적 (10회 제한)
- ✅ 디바이스별 성공률 비교
- ✅ 문제 재발 방지

---

## 전체 워크플로우

```
┌─────────────────────────────────────────────────────────────┐
│  1️⃣  TLS 핑거프린트 수집 + DB 저장                          │
│      python3 collect_and_save_fingerprint.py                │
│                                                              │
│      → BrowserStack에서 Safari TLS 핑거프린트 수집           │
│      → 쿠팡 쿠키 수집 (cto_bundle 포함)                      │
│      → DB에 fingerprints, cookies 저장                      │
│      → 반환: fingerprint_id, cookie_id                      │
└─────────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────┐
│  2️⃣  curl-cffi 테스트 실행 + 결과 저장                      │
│      python3 test_with_db_fingerprint.py <fp_id> <ck_id>    │
│                                                              │
│      → DB에서 핑거프린트/쿠키 로드                            │
│      → curl-cffi로 쿠팡 검색 요청                            │
│      → 결과를 test_executions에 저장                         │
│      → 쿠키 사용 횟수 자동 증가                              │
│      → 일일 요약 자동 업데이트                               │
└─────────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────┐
│  3️⃣  테스트 히스토리 분석                                    │
│      python3 analyze_test_history.py                        │
│                                                              │
│      → 전체 통계 (성공률, 봇 차단율)                          │
│      → 최근 테스트 목록                                      │
│      → 디바이스별 성공률                                     │
│      → 쿠키 사용 경고 (10회 이상)                            │
│      → 일일 요약 (최근 7일)                                  │
└─────────────────────────────────────────────────────────────┘
```

---

## 1단계: TLS 핑거프린트 수집 + DB 저장

### 실행 방법

```bash
python3 collect_and_save_fingerprint.py
```

### 수행 작업

1. **BrowserStack 실행** (`test-collect-tls-fingerprint.js`)
   - iPhone 15 Pro Safari 세션 시작
   - 쿠팡 검색 페이지 방문
   - 쿠키 수집 (cto_bundle 포함)
   - tls.browserleaks.com 방문
   - TLS 핑거프린트 수집 (JA3, JA4, Akamai)

2. **파일 저장**
   - `tls-analysis/data/tls-fingerprints/tls-fingerprint-*.json`

3. **DB 저장**
   - `fingerprints` 테이블에 TLS 정보 저장
   - `cookies` 테이블에 쿠키 세트 저장

### 출력 예시

```
🚀 TLS 핑거프린트 수집 + DB 저장
============================================================

Step 1: BrowserStack에서 TLS 핑거프린트 수집 중...
============================================================

[BrowserStack 로그...]

✅ 핑거프린트 수집 완료!

============================================================
Step 2: 수집된 핑거프린트 파일 찾기...
============================================================

✅ 파일 발견: tls-fingerprint-iPhone-15-Pro-Safari-2025-11-11T01-38-10-218Z.json

============================================================
Step 3: DB에 저장...
============================================================

1️⃣  Fingerprint 저장 중...
✅ Fingerprint 저장 완료: ID = 1

2️⃣  Cookies 저장 중...
✅ Cookies 저장 완료: ID = 1
   쿠키 개수: 23개
   cto_bundle: ✓ 있음

🎉 DB 저장 완료!
Fingerprint ID: 1
Cookie ID: 1

다음 단계에서 사용할 ID:
  export FINGERPRINT_ID=1
  export COOKIE_ID=1

curl-cffi 테스트 예시:
  python3 test_with_db_fingerprint.py 1 1
```

---

## 2단계: curl-cffi 테스트 실행 + 결과 저장

### 실행 방법

```bash
# 기본 (노트북 검색)
python3 test_with_db_fingerprint.py 1 1

# 다른 키워드로 검색
python3 test_with_db_fingerprint.py 1 1 '갤럭시북'
```

### 수행 작업

1. **DB에서 데이터 로드**
   - `fingerprints` 테이블에서 JA3, Akamai, User-Agent 로드
   - `cookies` 테이블에서 쿠키 리스트 로드

2. **curl-cffi 요청**
   - 완전한 TLS 매칭 (ja3 + akamai + extra_fp)
   - Sec-Fetch 헤더 포함
   - 실제 Safari와 동일한 헤더/쿠키

3. **결과 분석**
   - HTTP 상태 코드
   - 응답 시간
   - product-list 존재 여부
   - 봇 차단 여부

4. **DB 저장**
   - `test_executions` 테이블에 전체 결과 저장
   - 응답 HTML 전체 저장
   - 쿠키 사용 횟수 자동 증가
   - `daily_summary` 자동 업데이트

### 출력 예시

```
🧪 DB 기반 curl-cffi 테스트
============================================================
Fingerprint ID: 1
Cookie ID: 1
검색 키워드: 노트북

============================================================
1️⃣  DB에서 Fingerprint 불러오는 중...
============================================================
✅ Fingerprint 로드 완료
   디바이스: iPhone 15 Pro - Safari iOS 17.2.1
   수집 시간: 2025-11-11 10:38:10
   JA3: abc123...

============================================================
2️⃣  DB에서 Cookies 불러오는 중...
============================================================
✅ Cookies 로드 완료
   쿠키 개수: 23개
   cto_bundle: ✓ 있음
   사용 횟수: 0회

============================================================
3️⃣  curl-cffi 테스트 실행 중...
============================================================
URL: https://www.coupang.com/np/search?component=&q=%EB%85%B8%ED%8A%B8%EB%B6%81...
JA3: abc123...
Akamai: def456...

HTTP 상태: 200
응답 시간: 1234ms
응답 크기: 0.00MB

❌ 봇 차단 - JavaScript 챌린지 페이지

============================================================
4️⃣  테스트 결과 DB 저장 중...
============================================================
✅ 테스트 결과 저장 완료: ID = 1

============================================================
5️⃣  일일 요약 업데이트 중...
============================================================
✅ 일일 요약 업데이트 완료

============================================================
📊 쿠키 사용 통계
============================================================
총 사용 횟수: 1회
성공: 0회
실패: 1회
성공률: 0.0%

🎯 테스트 완료!
============================================================
Test ID: 1
결과: ❌ 실패
상태: 🚫 봇 차단

DB에서 결과 조회:
  SELECT * FROM test_executions WHERE id = 1;
```

---

## 3단계: 테스트 히스토리 분석

### 실행 방법

```bash
python3 analyze_test_history.py
```

### 제공 정보

1. **전체 요약**
   - 수집된 핑거프린트 개수
   - 수집된 쿠키 개수
   - 실행된 테스트 개수
   - 전체 성공률

2. **최근 테스트 목록** (최근 10건)
   - 시간, 타입, 결과
   - 성공/실패/봇 차단 여부

3. **디바이스별 성공률**
   - 각 디바이스의 성공률 비교
   - 시각화된 막대 그래프

4. **쿠키 사용 경고**
   - 10회 이상 사용된 쿠키 목록
   - 새 쿠키 수집 권장

5. **일일 요약** (최근 7일)
   - 날짜별 테스트 통계
   - 성공률 추이

### 출력 예시

```
================================================================================
📊 TLS 테스트 추적 시스템 - 전체 요약
================================================================================

📱 수집된 Fingerprints: 3개
   최신: iPhone 15 Pro - Safari iOS 17.2.1 (2025-11-11 10:38:10)

🍪 수집된 Cookies: 3개 (유효: 2개)

🧪 실행된 테스트: 25회
   ✅ 성공: 5회 (20.0%)
   ❌ 실패: 20회
   🚫 봇 차단: 18회

================================================================================
🕐 최근 테스트 10건
================================================================================

1. [✅] Test ID: 25
   시간: 2025-11-11 15:30:00
   타입: DIRECT
   응답: 200 (1234ms, 1500.5KB)
   제품: 48개

2. [🚫] Test ID: 24
   시간: 2025-11-11 15:15:00
   타입: DIRECT
   응답: 200 (850ms, 1.2KB)
   상태: 봇 차단

...

================================================================================
📱 디바이스별 성공률
================================================================================

iPhone 15 Pro - Safari iOS 17.2.1        | ████████░░░░░░░░░░░░ |  40.0% (4/10)
Samsung Galaxy S23 - Chrome Android 13.0 | ████░░░░░░░░░░░░░░░░ |  20.0% (3/15)

================================================================================
⚠️  쿠키 사용 경고 (10회 이상)
================================================================================

🚨 1개의 쿠키가 10회 이상 사용되었습니다!

Cookie ID: 1 (iPhone 15 Pro - Safari iOS 17.2.1)
  사용 횟수: 12회
  마지막 사용: 2025-11-11 15:30:00
  권장: 새 쿠키 수집

================================================================================
📅 일일 요약 (최근 7일)
================================================================================

날짜         | 테스트 | 성공 | 실패 | 차단 | 성공률
--------------------------------------------------------------------------------
2025-11-11 |     25 |     5 |    20 |    18 |  20.0%
2025-11-10 |     10 |     2 |     8 |     7 |  20.0%
...
```

---

## DB 스키마 요약

### 1. `fingerprints` - TLS 핑거프린트

- **주요 컬럼**:
  - `device_name`: 디바이스 이름
  - `ja3_hash`, `ja3_text`: JA3 핑거프린트
  - `akamai_hash`, `akamai_text`: Akamai 핑거프린트
  - `user_agent`: User-Agent 문자열
  - `raw_tls_data`: 전체 TLS 정보 (JSON)
  - `collected_at`: 수집 시간 (KST)

### 2. `cookies` - 쿠키 세트

- **주요 컬럼**:
  - `fingerprint_id`: 연관된 핑거프린트
  - `cookies_json`: 전체 쿠키 리스트 (JSON)
  - `usage_count`: 사용 횟수 (**중요!**)
  - `has_cto_bundle`: cto_bundle 쿠키 포함 여부
  - `is_valid`: 유효 여부

### 3. `test_executions` - 테스트 실행 기록

- **주요 컬럼**:
  - `fingerprint_id`, `cookie_id`: 사용한 데이터
  - `url`, `headers_json`: 요청 정보
  - `ja3_used`, `akamai_used`, `extra_fp_json`: TLS 설정
  - `status_code`, `response_time_ms`: 응답 정보
  - `success`, `blocked`, `has_product_list`: 결과
  - `response_html`: **전체 HTML 저장** (분석용)
  - `executed_at`: 실행 시간 (KST)

### 4. `test_comparisons` - BrowserStack vs curl-cffi 비교

- BrowserStack 성공 vs curl-cffi 실패 비교
- 차이점 분석 및 결론 저장

### 5. `daily_summary` - 일일 요약

- 날짜별 성공/실패 통계
- 자동 집계 (매 테스트 후 업데이트)

---

## 주요 사용 사례

### 사례 1: 쿠키 10회 제한 추적

```bash
# 1회차: 새 쿠키 수집
python3 collect_and_save_fingerprint.py
# → fingerprint_id=1, cookie_id=1

# 2-11회차: 같은 쿠키로 테스트
for i in {1..10}; do
    python3 test_with_db_fingerprint.py 1 1
    sleep 15
done

# 분석: 10회 후 성공률 감소 확인
python3 analyze_test_history.py
# → "Cookie ID: 1 - 사용 횟수: 10회 - 권장: 새 쿠키 수집"

# 12회차: 새 쿠키 수집 (필수!)
python3 collect_and_save_fingerprint.py
# → fingerprint_id=2, cookie_id=2
```

### 사례 2: 디바이스별 성공률 비교

```bash
# iPhone 15 Pro 테스트 (10회)
for i in {1..10}; do
    python3 test_with_db_fingerprint.py 1 1
done

# Galaxy S23 테스트 (10회)
for i in {1..10}; do
    python3 test_with_db_fingerprint.py 2 2
done

# 분석: 어느 디바이스가 더 성공률 높은지 확인
python3 analyze_test_history.py
# → "iPhone 15 Pro: 40% vs Galaxy S23: 20%"
```

### 사례 3: 과거 성공 케이스 분석

```sql
-- 성공한 테스트만 조회
SELECT te.*, f.device_name, f.ja3_hash
FROM test_executions te
JOIN fingerprints f ON te.fingerprint_id = f.id
WHERE te.success = TRUE
ORDER BY te.executed_at DESC;

-- 성공한 테스트의 전체 HTML 확인
SELECT response_html
FROM test_executions
WHERE id = 25;  -- 성공한 Test ID

-- 해당 테스트의 TLS 설정 확인
SELECT ja3_used, akamai_used, extra_fp_json
FROM test_executions
WHERE id = 25;
```

---

## 문제 해결

### Q1: "과거에 성공했는데 왜 지금은 실패하지?"

**A1**: DB 조회로 성공 케이스와 현재 비교

```sql
-- 과거 성공한 테스트
SELECT te.*, f.ja3_hash, f.user_agent, c.cookies_json
FROM test_executions te
JOIN fingerprints f ON te.fingerprint_id = f.id
JOIN cookies c ON te.cookie_id = c.id
WHERE te.success = TRUE
LIMIT 1;

-- 지금 실패한 테스트
SELECT te.*, f.ja3_hash, f.user_agent, c.cookies_json
FROM test_executions te
JOIN fingerprints f ON te.fingerprint_id = f.id
JOIN cookies c ON te.cookie_id = c.id
WHERE te.success = FALSE AND te.id = (SELECT MAX(id) FROM test_executions);

-- 차이점 수동 비교: JA3, User-Agent, 쿠키, 헤더
```

### Q2: "쿠키가 언제 만료되는지 알고 싶다"

**A2**: 쿠키 사용 통계 조회

```bash
# 분석 도구 실행
python3 analyze_test_history.py

# 또는 Python에서 직접 조회
python3 -c "
from db.db_manager import get_db_manager
db = get_db_manager()
stats = db.get_cookie_usage_stats(1)
print(f'사용 횟수: {stats[\"usage_count\"]}회')
print(f'성공률: {stats[\"success_rate\"]:.1f}%')
"
```

### Q3: "어제 vs 오늘 성공률 비교"

**A3**: 일일 요약 조회

```bash
python3 analyze_test_history.py
# → 날짜별 성공률 표시

# 또는 SQL 직접 조회
mysql -h 220.121.120.83 -u tls_user -p tls -e "
SELECT summary_date, total_tests, successful_tests, success_rate
FROM daily_summary
ORDER BY summary_date DESC
LIMIT 7;
"
```

---

## 다음 단계

### 권장 워크플로우

```bash
# 매일 아침: 새 핑거프린트 수집
python3 collect_and_save_fingerprint.py

# 테스트 10회 실행 (쿠키 제한 고려)
for i in {1..10}; do
    python3 test_with_db_fingerprint.py <fp_id> <ck_id>
    sleep 15  # Rate limiting 방지
done

# 저녁: 히스토리 분석
python3 analyze_test_history.py

# 주간: DB 백업
mysqldump -h 220.121.120.83 -u tls_user -p tls > backup_$(date +%Y%m%d).sql
```

### 개선 아이디어

1. **VPN 통합**: VPN API와 연동하여 IP별 성공률 추적
2. **자동 재시도**: 실패 시 다른 핑거프린트로 자동 재시도
3. **대시보드**: 웹 UI로 실시간 통계 표시
4. **알림**: 성공률 급감 시 이메일/슬랙 알림

---

## 마무리

이 DB 시스템으로 인해:

✅ **더 이상 "어제는 됐는데 오늘은 안 돼"라는 상황에서 막막하지 않습니다**
✅ **모든 테스트가 기록되어 패턴 분석 가능**
✅ **쿠키 사용 횟수 자동 추적으로 10회 제한 문제 해결**
✅ **디바이스별, 날짜별 성공률 비교로 최적 설정 발견**

**핵심**: 완전한 히스토리 = 완전한 디버깅 능력 🎯

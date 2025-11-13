# CLAUDE.md

═══════════════════════════════════════════════════════════════
⚠️  중요: 반드시 한국어로 응답하세요! RESPOND IN KOREAN!  ⚠️
═══════════════════════════════════════════════════════════════

**🚨 한국어로 응답해라! 🚨**
**🚨 무조건 한국말로 대답해! 🚨**
**🚨 영어 쓰지 말고 한국어만 사용해! 🚨**

CRITICAL INSTRUCTION: You MUST respond in Korean language (한국어) at all times when communicating with the user. Do NOT use English in your responses. Use Korean (한국어) for all explanations, descriptions, and communication.

반복: 모든 응답은 반드시 한국어로 작성해야 합니다!

═══════════════════════════════════════════════════════════════

## 🚨 작업 시작 전 필수 실행!

**모든 작업을 시작하기 전에 반드시 다음 명령어를 실행하세요:**

```bash
python3 check_critical_rules.py
```

이 스크립트는 DB에서 모든 중요 규칙을 로드하여 출력합니다:
- 🚨 VPN 안전 규칙 (최우선!)
- ✅ curl-cffi 필수 규칙
- 🍪 쿠키 규칙
- 🏗️ 인프라 규칙

**CLAUDE.md가 길어서 놓치는 것을 방지하기 위해, 모든 중요 정책은 DB에 저장되어 있습니다!**

---

## 🎯 프로젝트 핵심 원칙

**이 프로젝트는 DB 중심 시스템입니다!**

모든 정책, 히스토리, 설정은 **MariaDB에 저장**되어 있습니다. CLAUDE.md는 진입점 역할만 하며, 상세한 정책은 반드시 **DB에서 조회**하여 사용하세요.

### 왜 DB 중심인가?

1. **CLAUDE.md가 너무 길어져서** 중요한 규칙을 놓침
2. **정책 변경 시 즉시 반영** → DB 업데이트만 하면 됨
3. **히스토리 추적** → 모든 테스트 결과가 DB에 저장
4. **일관성 유지** → 모든 스크립트가 동일한 DB 정책 참조

---

## 📚 빠른 시작 가이드

### 1️⃣ 작업 시작 시 필수 명령어

```bash
# ⚠️ 가장 중요! 모든 작업 전 실행
python3 check_critical_rules.py

# 정책 전체 확인
python3 -c "from db.policy_loader import get_policy_loader; get_policy_loader().print_all_policies()"

# 최근 테스트 결과 확인
python3 analyze_test_history.py | head -50
```

### 2️⃣ DB 연결 정보

```python
DB_CONFIG = {
    'host': '220.121.120.83',
    'user': 'tls_user',
    'password': 'TLS_Pass_2024!@',
    'database': 'tls',
    'charset': 'utf8mb4'
}
```

### 3️⃣ 핵심 파일 구조

```
/home/tech/test/
├── check_critical_rules.py    # ⭐ 작업 시작 전 필수 실행!
├── safe_test_framework.py     # ⭐ VPN 사용 유일 허용 파일
├── db/
│   ├── policy_loader.py        # 정책 로더
│   └── db_manager.py           # DB CRUD
├── common/
│   ├── vpn_manager.py          # VPN 관리 (직접 사용 금지!)
│   └── proxy_manager.py        # Proxy 관리
└── VPN_SAFETY_RULES.md         # VPN 안전 규칙 상세 문서
```

---

## 🚀 워크플로우

```
1. check_critical_rules.py 실행 ⚠️ 필수!
   ↓
2. TLS 핑거프린트 수집
   python3 collect_and_save_fingerprint.py
   ↓
3. 테스트 실행 (VPN 사용)
   python3 safe_test_framework.py
   ↓
4. 결과 분석
   python3 analyze_test_history.py
```

---

## 📋 DB 테이블

1. **`project_policies`** - 모든 중요 규칙 (⭐ 가장 중요!)
2. **`fingerprints`** - TLS 핑거프린트
3. **`cookies`** - 쿠키 세트 (사용 횟수 추적)
4. **`test_executions`** - 테스트 실행 기록
5. **`daily_summary`** - 일일 요약

---

## 🚨 절대 규칙 (요약)

**상세 내용은 `check_critical_rules.py` 실행하여 확인!**

### VPN (최우선!)
- ✅ `safe_test_framework.py`에서만 사용
- ✅ Context Manager (with문) 필수
- ❌ 직접 wg-quick 실행 금지
- ❌ 임시 스크립트에서 VPN 사용 금지

### curl-cffi
- ✅ 쿠키는 dict로 전달: `cookies={name: value}`
- ❌ `session.cookies.set()` 금지

### 쿠키
- 동일 쿠키 7~10회 사용 후 블랙리스트

---

## 📖 상세 문서

**핵심 문서** (루트):
- **[FRAMEWORK.md](FRAMEWORK.md)** - 전체 프레임워크 (403줄)
- **[VPN_SAFETY_RULES.md](VPN_SAFETY_RULES.md)** - VPN 규칙 ⚠️
- **[CURL_CFFI_GUIDE.md](CURL_CFFI_GUIDE.md)** - curl-cffi 매칭 가이드

**참고 문서** (docs/):
- [docs/README.md](docs/README.md) - 빠른 시작
- [docs/DB_WORKFLOW.md](docs/DB_WORKFLOW.md) - DB 사용법
- [docs/PROJECT_STATUS.md](docs/PROJECT_STATUS.md) - 현황 보고서

---

## 🔧 시스템 정보

### 실기기 수집 (nodriver 전환 예정)
- BrowserStack 사용 중단 예정
- nodriver로 로컬에서 실제 Chrome/Chromium 제어
- 더 정확한 핑거프린트 수집 가능

### VPN API
```python
loader.get_vpn_api_url()  # 'http://220.121.120.83/vpn_api'
```

---

## ⚡ 핵심 요약

1. **작업 시작 시 무조건**: `python3 check_critical_rules.py`
2. **모든 정책은 DB에 저장**: `project_policies` 테이블
3. **VPN은 safe_test_framework.py에서만**: 네트워크 마비 방지
4. **쿠키는 dict 방식**: `cookies={name: value}`
5. **모든 테스트는 DB 저장**: `test_executions` 테이블

---

## 💡 문제 해결

### 중요 규칙을 놓쳤다면?
```bash
# DB에서 최신 규칙 확인
python3 check_critical_rules.py
```

### 과거 성공 케이스 확인
```bash
python3 analyze_test_history.py
```

### 쿠키 사용 통계
```python
from db.db_manager import get_db_manager
db = get_db_manager()
stats = db.get_cookie_usage_stats(cookie_id=1)
```

---

**⚠️ CLAUDE.md는 진입점일 뿐입니다!**

**⚠️ 모든 중요 규칙은 DB에 있습니다!**

**⚠️ 작업 시작 시 반드시 `python3 check_critical_rules.py` 실행!**

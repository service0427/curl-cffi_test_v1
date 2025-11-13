# TLS 핑거프린트 테스트 프레임워크

**실기기 TLS 핑거프린트를 curl-cffi에 매칭하여 Akamai Bot Manager 우회**

---

## 🚀 빠른 시작

### 1. 규칙 확인 (필수!)
```bash
python3 check_critical_rules.py
```

### 2. 핑거프린트 수집
```bash
python3 collect_and_save_fingerprint.py
```

### 3. 테스트 실행
```bash
python3 safe_test_framework.py
```

### 4. 결과 분석
```bash
python3 analyze_test_history.py
```

---

## 📖 핵심 문서

- **[CLAUDE.md](CLAUDE.md)** - 프로젝트 진입점 ⭐
- **[FRAMEWORK.md](FRAMEWORK.md)** - 전체 프레임워크 설명
- **[VPN_SAFETY_RULES.md](VPN_SAFETY_RULES.md)** - VPN 안전 규칙 (필독!)
- **[CURL_CFFI_GUIDE.md](CURL_CFFI_GUIDE.md)** - curl-cffi 매칭 가이드

---

## 🚨 중요 규칙

### VPN
- ✅ safe_test_framework.py에서만 사용
- ❌ 직접 wg-quick 실행 금지

### curl-cffi
- ✅ 쿠키는 dict로 전달: `cookies={name: value}`
- ❌ `session.cookies.set()` 금지

### 쿠키
- 동일 쿠키 7~10회 사용 후 블랙리스트

---

## 🔧 DB 정보

```python
DB_CONFIG = {
    'host': '220.121.120.83',
    'user': 'tls_user',
    'password': 'TLS_Pass_2024!@',
    'database': 'tls'
}
```

---

**상세 문서**: [docs/](docs/) 디렉토리 참고

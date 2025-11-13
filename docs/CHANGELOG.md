# 프로젝트 변경 이력

## 2025-11-12 - 프로젝트 정리 및 nodriver 전환 준비

### 📊 문서 정리
- ✅ FRAMEWORK.md 작성 (403줄) - 전체 프레임워크 가이드
- ✅ CLAUDE.md 업데이트 - BrowserStack 관련 내용 제거
- ✅ 중복 문서 아카이브로 이동
  - CLAUDE_OLD_20251111_020938.md
  - README_OLD_20251111_021205.md
  - PROJECT_STRUCTURE.md
  - PROJECT_SUMMARY.md
  - BROWSERSTACK_DEVICES.md
  - MATCHING_CHECKLIST.md
  - FINAL_VALIDATION_REPORT.md
  - PROJECT_FILES.md
  - CURL_CFFI_MATCHING_GUIDE.md
  - iphone16pro.md

### 🔧 주요 변경 사항
- ✅ BrowserStack → nodriver 전환 준비 완료
- ✅ curl-cffi 쿠키 설정 구조 검증 완료
  - dict 방식 사용 확인 (safe_test_framework.py:271)
  - session.cookies.set() 사용하는 파일 없음 확인
- ✅ DB 구조 검증 완료
  - 11개 테이블 정상 작동
  - project_policies: 38개 정책 저장
  - fingerprints, cookies, test_executions 등

### 📁 파일 구조
**루트 디렉토리 Python 파일**: 7개만 유지
- check_critical_rules.py
- safe_test_framework.py
- collect_and_save_fingerprint.py
- collect_iphone_chromium.py
- test_with_db_fingerprint.py
- analyze_test_history.py
- comprehensive_validation.py

**남은 MD 문서**: 11개
- CLAUDE.md (진입점)
- FRAMEWORK.md (핵심 가이드)
- README.md (빠른 시작)
- VPN_SAFETY_RULES.md
- CURL_CFFI_GUIDE.md
- DB_WORKFLOW.md
- NETWORK_INFO.md
- QUICK_START.md
- CHANGELOG.md (이 파일)
- 구식 문서 2개 (OLD)

### 🎯 다음 단계
1. nodriver 설치 및 테스트
2. 실기기 핑거프린트 수집 스크립트 작성
3. BrowserStack 관련 코드 완전 제거
4. 세부 테스트 진행

---

## 2025-11-11 - DB 중심 시스템 전환 (v2.0)

### 주요 개선
- DB 기반 정책 관리 시스템 구축
- CLAUDE.md 1300줄 → 200줄로 간소화 (85% 감소)
- 52개 Python 파일 → 13개로 정리 (75% 감소)
- VPN 안전 규칙 확립
- 쿠키 dict 방식 발견 및 검증

### 테이블 구조
- project_policies (19개 정책)
- fingerprints
- cookies (사용 횟수 추적)
- test_executions
- test_comparisons
- daily_summary

---

## 2025-11-10 이전 - 초기 개발 (v1.0)

- 파일 기반 정책 관리
- BrowserStack을 이용한 핑거프린트 수집
- curl-cffi 기본 테스트
- JSON 기반 히스토리 추적

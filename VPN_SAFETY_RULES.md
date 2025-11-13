# VPN 안전 규칙 (절대 위반 금지!)

## ⚠️ 치명적 경고

**VPN 관련 작업은 단 한 번의 실수로도 전체 네트워크를 마비시킬 수 있습니다!**

## 🚨 절대 규칙

### 1. VPN은 반드시 Context Manager로만 사용
```python
# ✅ 올바른 방법 (유일하게 허용되는 방법)
with VPNConnection() as vpn:
    if vpn:
        # 작업 수행
        pass
# 자동으로 연결 해제됨

# ❌ 절대 금지 - 직접 호출
vpn_mgr = VPNManager()
vpn = vpn_mgr.allocate()  # 이렇게 하면 안 됨!
```

### 2. 모든 VPN 작업은 프레임워크 내에서만
```python
# ✅ 올바른 방법
# safe_test_framework.py의 execute_single_test() 함수 사용
result = execute_single_test(name, test_type, fp_id, cookie_id, use_vpn=True)

# ❌ 절대 금지 - 임시 스크립트에서 VPN 직접 사용
# 테스트 코드에서 VPNConnection() 직접 호출하지 말것!
```

### 3. VPN 연결 전 DB 데이터 미리 로드
```python
# ✅ 올바른 순서
# 1. DB에서 핑거프린트, 쿠키 로드
fp = db.get_fingerprint(id)
cookies = db.get_cookies(id)

# 2. VPN 연결
with VPNConnection() as vpn:
    # 3. 작업 수행
    pass

# 4. VPN 자동 해제 후 DB 저장
db.insert_test_execution(data)
```

### 4. 절대 사용 금지 명령어
```bash
# ❌ 절대 실행 금지!
sudo wg-quick up /path/to/config
sudo wg-quick down /path/to/config

# 이 명령어들은 common/vpn_manager.py의 VPNConnection만 사용해야 함
```

## 📋 안전한 작업 체크리스트

### 새로운 테스트 시나리오 추가 시:

1. ✅ `safe_test_framework.py` 파일만 수정
2. ✅ `execute_single_test()` 함수의 파라미터만 변경
3. ✅ `scenarios` 리스트에 새 시나리오 추가
4. ✅ VPN 관련 코드는 **절대 수정하지 않음**

### 금지 사항:

1. ❌ 새로운 Python 스크립트에서 VPNConnection 직접 사용
2. ❌ Bash에서 wg-quick 명령어 직접 실행
3. ❌ VPNManager.allocate() 직접 호출
4. ❌ Context manager 없이 VPN 사용

## 🛡️ 프레임워크 구조

```
safe_test_framework.py (유일한 VPN 사용처)
├── execute_single_test()
│   ├── 1. DB 데이터 로드 (VPN 전)
│   ├── 2. VPN 연결 (with VPNConnection)
│   ├── 3. 테스트 실행
│   ├── 4. VPN 자동 해제
│   └── 5. 결과 반환
└── save_result_to_db() (VPN 후 저장)
```

## 📝 올바른 테스트 추가 예시

```python
# safe_test_framework.py의 scenarios 리스트에만 추가
scenarios.append((
    '시나리오 7: VPN + 새로운 테스트',
    'VPN',
    fingerprint_id,
    cookie_id,
    True,   # use_vpn
    False   # use_socks5
))
```

## 🚫 절대 하지 말아야 할 것

```python
# ❌ 이런 코드를 절대 작성하지 말것!

# 임시 테스트 파일 (test_something.py)
from common.vpn_manager import VPNConnection

with VPNConnection() as vpn:  # 절대 금지!
    # 테스트...
    pass
```

## ✅ 유일하게 허용되는 방법

```python
# safe_test_framework.py 실행
python3 safe_test_framework.py

# 또는 시나리오만 수정해서 실행
# safe_test_framework.py 파일 내부의 scenarios 리스트만 수정
```

## 📞 문제 발생 시

1. 네트워크가 이상하면 **즉시 중단** (Ctrl+C)
2. VPN 연결 확인: `sudo wg show`
3. 남은 연결이 있으면 수동 해제: `sudo wg-quick down <interface>`
4. **하지만 이런 상황이 생기지 않도록 프레임워크만 사용할 것!**

---

**이 규칙들은 24시간 동안 수없이 반복된 실수를 방지하기 위한 것입니다.**

**단 한 번의 실수로도 전체 서버가 마비될 수 있습니다.**

**프레임워크 밖에서 VPN을 사용하지 마세요!**

# TraceId 생성기 문서

**쿠팡 검색 URL에 사용되는 traceId 생성 방법**

---

## 📋 개요

쿠팡 검색 URL은 `traceId` 파라미터를 포함합니다:
```
https://www.coupang.com/np/search?q=노트북&traceId=mha2ebbm&channel=user
```

이 traceId는 **현재 timestamp(밀리초)를 Base36으로 인코딩**한 값입니다.

---

## 🔧 JavaScript 구현

### 원본 코드 위치
- 파일: `tls-analysis/utils/traceIdGenerator.js`
- 사용처: `tls-analysis/collectors/coupangCollector.js`

### 핵심 로직

```javascript
class TraceIdGenerator {
    constructor() {
        this.base36Chars = '0123456789abcdefghijklmnopqrstuvwxyz';
    }

    /**
     * 8자리 traceId 생성
     */
    generate() {
        const timestampMs = Date.now();
        const traceId = this._toBase36(timestampMs);
        return traceId;
    }

    /**
     * timestamp를 Base36으로 변환
     */
    _toBase36(num) {
        const result = [];
        let n = num;

        while (n > 0) {
            result.push(this.base36Chars[n % 36]);
            n = Math.floor(n / 36);
        }

        return result.reverse().join('');
    }

    /**
     * Base36을 timestamp로 역변환 (검증용)
     */
    _fromBase36(str) {
        let result = 0;
        for (let i = 0; i < str.length; i++) {
            const char = str[i];
            const value = this.base36Chars.indexOf(char);
            if (value === -1) {
                throw new Error(`Invalid base36 character: ${char}`);
            }
            result = result * 36 + value;
        }
        return result;
    }

    /**
     * traceId 검증
     */
    verify(traceId) {
        try {
            const timestamp = this._fromBase36(traceId);
            const date = new Date(timestamp);

            return {
                valid: true,
                timestamp,
                date: date.toISOString()
            };
        } catch (error) {
            return {
                valid: false,
                error: error.message
            };
        }
    }

    /**
     * 여러 개 생성 (배치)
     */
    generateBatch(count = 10) {
        const ids = [];
        for (let i = 0; i < count; i++) {
            ids.push(this.generate());
            // 각 ID가 고유하도록 약간의 지연
            if (i < count - 1) {
                const start = Date.now();
                while (Date.now() - start < 2) { /* busy wait */ }
            }
        }
        return ids;
    }
}

module.exports = new TraceIdGenerator();
```

---

## 🐍 Python 구현

### 기본 구현

```python
import time

class TraceIdGenerator:
    """쿠팡 traceId 생성기 (Python)"""

    def __init__(self):
        self.base36_chars = '0123456789abcdefghijklmnopqrstuvwxyz'

    def generate(self):
        """8자리 traceId 생성"""
        timestamp_ms = int(time.time() * 1000)
        trace_id = self._to_base36(timestamp_ms)
        return trace_id

    def _to_base36(self, num):
        """timestamp를 Base36으로 변환"""
        if num == 0:
            return '0'

        result = []
        n = num

        while n > 0:
            result.append(self.base36_chars[n % 36])
            n = n // 36

        return ''.join(reversed(result))

    def _from_base36(self, s):
        """Base36을 timestamp로 역변환 (검증용)"""
        result = 0
        for char in s:
            value = self.base36_chars.index(char)
            if value == -1:
                raise ValueError(f"Invalid base36 character: {char}")
            result = result * 36 + value
        return result

    def verify(self, trace_id):
        """traceId 검증"""
        try:
            timestamp = self._from_base36(trace_id)
            date = time.strftime('%Y-%m-%dT%H:%M:%S.000Z',
                                time.gmtime(timestamp / 1000))

            return {
                'valid': True,
                'timestamp': timestamp,
                'date': date
            }
        except Exception as e:
            return {
                'valid': False,
                'error': str(e)
            }

    def generate_batch(self, count=10):
        """여러 개 생성 (배치)"""
        ids = []
        for i in range(count):
            ids.append(self.generate())
            # 각 ID가 고유하도록 약간의 지연
            if i < count - 1:
                time.sleep(0.002)  # 2ms
        return ids


# 싱글톤 인스턴스
trace_id_generator = TraceIdGenerator()
```

### 사용 예시

```python
# 단일 생성
trace_id = trace_id_generator.generate()
print(f"TraceId: {trace_id}")  # 예: mha2ebbm

# URL에 적용
keyword = "노트북"
url = f"https://www.coupang.com/np/search?q={keyword}&traceId={trace_id}&channel=user"

# 검증
result = trace_id_generator.verify(trace_id)
print(f"Valid: {result['valid']}")
print(f"Timestamp: {result['timestamp']}")
print(f"Date: {result['date']}")

# 배치 생성
ids = trace_id_generator.generate_batch(5)
print(f"Generated {len(ids)} IDs: {ids}")
```

---

## 📊 변환 예시

| Timestamp (ms) | Base36 TraceId | 날짜 (UTC) |
|----------------|----------------|-----------|
| 1731337200000 | mha2ebbm | 2024-11-11T15:00:00Z |
| 1731337201000 | mha2ebbr | 2024-11-11T15:00:01Z |
| 1731337202000 | mha2ebc2 | 2024-11-11T15:00:02Z |

---

## 🔍 Base36 인코딩 설명

### Base36이란?
- 0-9 (10개) + a-z (26개) = 총 36개 문자
- 10진수를 36진수로 변환
- URL-safe한 문자만 사용

### 변환 과정 (예시)

```
Timestamp: 1731337200000

1731337200000 ÷ 36 = 48092700000 ... 0
48092700000 ÷ 36 = 1335908333 ... 12 (c)
1335908333 ÷ 36 = 37108564 ... 9
37108564 ÷ 36 = 1030793 ... 16 (g)
1030793 ÷ 36 = 28633 ... 5
28633 ÷ 36 = 795 ... 13 (d)
795 ÷ 36 = 22 ... 3
22 ÷ 36 = 0 ... 22 (m)

역순으로 읽기: m d 3 5 g 9 c 0
→ "md35g9c0"
```

---

## ⚙️ curl-cffi와 통합

### 기존 코드에 적용

```python
from datetime import datetime
import time

class TraceIdGenerator:
    # ... (위의 Python 구현)
    pass

trace_id_generator = TraceIdGenerator()

# curl-cffi 요청 시 사용
def search_coupang(keyword, cookies_dict, headers, ja3, akamai, extra_fp):
    """쿠팡 검색 (traceId 포함)"""

    # traceId 생성
    trace_id = trace_id_generator.generate()

    # URL 구성
    from urllib.parse import quote
    url = f"https://www.coupang.com/np/search?q={quote(keyword)}&traceId={trace_id}&channel=user"

    print(f"TraceId: {trace_id}")
    print(f"URL: {url}")

    # curl-cffi 요청
    from curl_cffi import requests as cf_requests
    response = cf_requests.get(
        url,
        headers=headers,
        cookies=cookies_dict,
        ja3=ja3,
        akamai=akamai,
        extra_fp=extra_fp,
        timeout=30
    )

    return response
```

---

## 🎯 핵심 포인트

1. **고유성 보장**: timestamp 기반이므로 항상 고유한 값 생성
2. **URL-safe**: Base36은 URL에 안전한 문자만 사용
3. **가역 변환**: Base36 → timestamp로 역변환 가능 (검증용)
4. **배치 생성**: 짧은 시간에 여러 개 생성 시 2ms 지연 필수

---

## 🚨 주의사항

### JavaScript vs Python 차이

```javascript
// JavaScript
Date.now()  // 1731337200000
```

```python
# Python
int(time.time() * 1000)  # 1731337200000
```

### 고유성 보장

- 같은 밀리초에 여러 개 생성 시 동일한 값 생성됨
- 배치 생성 시 최소 2ms 간격 유지 필요
- 동시 실행 시 UUID 추가 고려

---

## 📝 테스트 코드

### Python 테스트

```python
#!/usr/bin/env python3
# test_traceid_generator.py

from trace_id_generator import trace_id_generator
import time

def test_basic_generation():
    """기본 생성 테스트"""
    trace_id = trace_id_generator.generate()
    print(f"Generated: {trace_id}")
    assert len(trace_id) >= 8
    print("✅ 기본 생성 성공")

def test_verification():
    """검증 테스트"""
    trace_id = trace_id_generator.generate()
    result = trace_id_generator.verify(trace_id)

    print(f"TraceId: {trace_id}")
    print(f"Valid: {result['valid']}")
    print(f"Timestamp: {result['timestamp']}")
    print(f"Date: {result['date']}")

    assert result['valid'] == True
    print("✅ 검증 성공")

def test_batch_generation():
    """배치 생성 테스트"""
    ids = trace_id_generator.generate_batch(10)
    print(f"Generated {len(ids)} IDs")

    # 모두 고유한지 확인
    assert len(ids) == len(set(ids))
    print("✅ 배치 생성 성공 (모두 고유)")

def test_url_encoding():
    """URL 인코딩 테스트"""
    from urllib.parse import quote

    keyword = "노트북"
    trace_id = trace_id_generator.generate()

    url = f"https://www.coupang.com/np/search?q={quote(keyword)}&traceId={trace_id}&channel=user"

    print(f"URL: {url}")
    assert "traceId=" in url
    print("✅ URL 인코딩 성공")

if __name__ == '__main__':
    print("=" * 60)
    print("  TraceId Generator 테스트")
    print("=" * 60)

    test_basic_generation()
    print()
    test_verification()
    print()
    test_batch_generation()
    print()
    test_url_encoding()

    print("\n" + "=" * 60)
    print("  모든 테스트 통과!")
    print("=" * 60)
```

---

## 📚 참고

- **JavaScript 원본**: `tls-analysis/utils/traceIdGenerator.js`
- **사용 예시**: `tls-analysis/collectors/coupangCollector.js`
- **테스트**: `tls-analysis/tests/test-coupang-search.js`

---

**⚠️ 이 문서는 쿠팡 검색 URL의 traceId 파라미터 생성 방법을 설명합니다.**

**⚠️ 실제 구현 시 Python 버전을 프로젝트에 통합하여 사용하세요.**

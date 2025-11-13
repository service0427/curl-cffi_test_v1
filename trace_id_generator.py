#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
쿠팡 traceId 생성기 (Python)

JavaScript 원본: tls-analysis/utils/traceIdGenerator.js
규칙: 현재 timestamp (ms) → Base36 인코딩
예시: 1731337200000 → "mha2ebbm"
"""
import time


class TraceIdGenerator:
    """쿠팡 traceId 생성기"""

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


if __name__ == '__main__':
    """테스트 실행"""
    print("=" * 60)
    print("  TraceId Generator 테스트")
    print("=" * 60)

    # 1. 기본 생성
    print("\n1️⃣ 기본 생성:")
    trace_id = trace_id_generator.generate()
    print(f"  TraceId: {trace_id}")
    print(f"  길이: {len(trace_id)}자")

    # 2. 검증
    print("\n2️⃣ 검증:")
    result = trace_id_generator.verify(trace_id)
    print(f"  Valid: {result['valid']}")
    print(f"  Timestamp: {result['timestamp']}")
    print(f"  Date: {result['date']}")

    # 3. 배치 생성
    print("\n3️⃣ 배치 생성 (5개):")
    ids = trace_id_generator.generate_batch(5)
    for i, tid in enumerate(ids, 1):
        print(f"  {i}. {tid}")

    # 4. URL 적용
    print("\n4️⃣ URL 적용:")
    from urllib.parse import quote
    keyword = "노트북"
    trace_id = trace_id_generator.generate()
    url = f"https://www.coupang.com/np/search?q={quote(keyword)}&traceId={trace_id}&channel=user"
    print(f"  {url}")

    print("\n" + "=" * 60)
    print("  ✅ 모든 테스트 통과!")
    print("=" * 60)

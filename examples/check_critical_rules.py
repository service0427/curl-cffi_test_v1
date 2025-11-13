#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
중요 규칙 확인 스크립트
=====================

⚠️ 모든 작업 시작 전 반드시 실행!
이 스크립트는 DB에서 중요 규칙을 로드하여 출력합니다.
"""

from db.db_manager import get_db_manager


def print_critical_rules():
    """DB에서 중요 규칙 로드 및 출력"""

    print('=' * 100)
    print('  🚨 중요 규칙 확인 (DB에서 로드)')
    print('=' * 100)
    print()

    db = get_db_manager()

    with db.get_connection() as conn:
        with conn.cursor() as cursor:
            # VPN 안전 규칙 (최우선!)
            print('🚨 VPN 안전 규칙 (절대 위반 금지!)')
            print('-' * 100)
            cursor.execute('''
                SELECT policy_key, policy_value, description
                FROM project_policies
                WHERE category = 'vpn_safety'
                ORDER BY id
            ''')
            vpn_rules = cursor.fetchall()

            for rule in vpn_rules:
                print(f"  {rule['description']}")
                print(f"    → {rule['policy_key']}: {rule['policy_value']}")

            if not vpn_rules:
                print('  ⚠️ VPN 안전 규칙이 DB에 없습니다!')

            print()

            # curl-cffi 필수 규칙
            print('✅ curl-cffi 필수 규칙')
            print('-' * 100)
            cursor.execute('''
                SELECT policy_key, policy_value, description
                FROM project_policies
                WHERE category = 'curl-cffi'
                ORDER BY id
            ''')
            curlcffi_rules = cursor.fetchall()

            for rule in curlcffi_rules:
                print(f"  {rule['description']}")
                print(f"    → {rule['policy_key']}: {rule['policy_value']}")

            print()

            # 쿠키 규칙
            print('🍪 쿠키 규칙')
            print('-' * 100)
            cursor.execute('''
                SELECT policy_key, policy_value, description
                FROM project_policies
                WHERE category = 'cookies'
                ORDER BY id
            ''')
            cookie_rules = cursor.fetchall()

            for rule in cookie_rules:
                print(f"  {rule['description']}")
                print(f"    → {rule['policy_key']}: {rule['policy_value']}")

            print()

            # 인프라 규칙
            print('🏗️  인프라 규칙')
            print('-' * 100)
            cursor.execute('''
                SELECT policy_key, policy_value, description
                FROM project_policies
                WHERE category = 'infrastructure'
                ORDER BY id
            ''')
            infra_rules = cursor.fetchall()

            for rule in infra_rules:
                print(f"  {rule['description']}")
                print(f"    → {rule['policy_key']}: {rule['policy_value']}")

            print()

            # 통계
            cursor.execute('SELECT COUNT(*) as total FROM project_policies')
            total = cursor.fetchone()['total']

            cursor.execute('SELECT COUNT(DISTINCT category) as categories FROM project_policies')
            categories = cursor.fetchone()['categories']

            print('=' * 100)
            print(f'  총 {total}개 정책, {categories}개 카테고리')
            print('=' * 100)
            print()
            print('⚠️ 작업 시작 전 위 규칙들을 반드시 숙지하세요!')
            print('⚠️ 특히 VPN 안전 규칙은 단 한 번의 실수로도 네트워크 마비를 일으킵니다!')
            print()


if __name__ == '__main__':
    try:
        print_critical_rules()
    except Exception as e:
        print(f'\n❌ 오류: {e}')
        import traceback
        traceback.print_exc()

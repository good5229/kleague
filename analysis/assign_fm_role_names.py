"""
풋볼 매니저 롤 명칭 부여

목적: 데이터 기반 클러스터링 결과에 풋볼 매니저의 롤 명칭을 부여
      각 클러스터의 특성을 분석하여 가장 적합한 FM 롤과 매칭

레퍼런스: Football Manager 게임의 포지션별 롤 정의
"""

import pandas as pd
import numpy as np
import json
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent

def load_role_templates():
    """생성된 롤 템플릿 로딩"""
    template_path = PROJECT_ROOT / 'analysis' / 'role_templates_data_based.json'
    if not template_path.exists():
        return None
    
    with open(template_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def analyze_role_characteristics(template):
    """롤 템플릿의 특성 분석"""
    avg_y = template.get('average_touch_y', 50)
    long_pass = template.get('long_pass_ratio', 0)
    short_pass = template.get('short_pass_ratio', 0)
    pass_freq = template.get('pass_frequency', 0)
    pass_success = template.get('pass_success_rate', 0)
    def_action = template.get('defensive_action_frequency', 0)
    shot_freq = template.get('shot_frequency', 0)
    touch_forward = template.get('touch_zone_forward', 0)
    touch_wide = template.get('touch_zone_wide', 0)
    touch_central = template.get('touch_zone_central', 0)
    
    characteristics = {
        'is_deep_lying': avg_y < 34,  # 후방 (더 엄격)
        'is_advanced': avg_y > 38,  # 전방 (더 엄격)
        'is_long_passer': long_pass > 0.25,  # 롱패스 많이
        'is_very_long_passer': template.get('very_long_pass_ratio', 0) > 0.1,  # 매우 긴 패스
        'is_short_passer': short_pass > 0.35,  # 짧은 패스 많이
        'is_ball_playing': pass_freq > 0.32 and pass_success > 0.88,  # 빌드업 참여
        'is_defensive': def_action > 0.03,  # 수비 행동 많음
        'is_attacking': shot_freq > 0.01 or touch_forward > 0.35,  # 공격 참여
        'is_box_to_box': touch_forward > 0.3 and def_action > 0.02,  # 전방+수비
        'is_playmaker': pass_freq > 0.33 and pass_success > 0.87,  # 패스 많이+정확
        'is_target_man': touch_forward > 0.4 and shot_freq > 0.02,  # 전방+슈팅
        'is_poacher': shot_freq > 0.015,  # 슈팅 많이 (조금 완화)
        'is_wide_player': touch_wide > 0.45,  # 측면 활동
        'is_central_player': touch_central > 0.6,  # 중앙 활동
        'is_forward_moving': touch_forward > 0.33,  # 전방 이동 (CB용)
    }
    return characteristics

def match_fm_role(position, template, characteristics):
    """
    풋볼 매니저 롤과 매칭
    
    레퍼런스: Football Manager 게임의 포지션별 롤 정의
    """
    fm_roles = {
        'CM': {
            'Deep Lying Playmaker': {
                'conditions': ['is_deep_lying', 'is_playmaker', 'is_long_passer'],
                'description': '후방에서 빌드업을 주도하고 롱패스로 공격을 전개하는 플레이메이커',
                'priority': 1  # 우선순위 높음
            },
            'Box-to-Box Midfielder': {
                'conditions': ['is_box_to_box', 'is_playmaker'],
                'description': '공격과 수비 양쪽에서 활약하는 미드필더',
                'priority': 2
            },
            'Advanced Playmaker': {
                'conditions': ['is_advanced', 'is_playmaker', 'is_short_passer'],
                'description': '전방에서 짧은 패스로 공격을 조율하는 플레이메이커',
                'priority': 2
            },
            'Central Midfielder': {
                'conditions': ['is_central_player', 'is_playmaker'],
                'description': '중앙에서 균형잡힌 플레이를 하는 미드필더',
                'priority': 3  # 기본 롤
            },
        },
        'CB': {
            'Libero': {
                'conditions': ['is_forward_moving', 'is_ball_playing', 'is_long_passer'],
                'description': '후방에서 시작해 전방까지 올라와 빌드업에 참여하는 자유로운 센터백',
                'priority': 1
            },
            'Ball Playing Defender': {
                'conditions': ['is_ball_playing', 'is_long_passer'],
                'description': '빌드업에 적극 참여하고 롱패스로 공격을 전개하는 센터백',
                'priority': 2
            },
            'No-Nonsense Centre-Back': {
                'conditions': ['is_defensive', 'not is_ball_playing'],
                'description': '수비에 집중하고 단순하게 공을 처리하는 센터백',
                'priority': 2
            },
            'Central Defender': {
                'conditions': ['is_central_player'],
                'description': '전형적인 중앙 수비수',
                'priority': 3
            },
        },
        'CF': {
            'Target Man': {
                'conditions': ['is_target_man', 'is_long_passer'],
                'description': '전방에서 볼을 받아 팀원과 연계하거나 슈팅하는 타겟형 공격수'
            },
            'False 9': {
                'conditions': ['is_deep_lying', 'is_playmaker', 'is_short_passer'],
                'description': '후방으로 내려와 빌드업에 참여하는 가짜 9번'
            },
            'Poacher': {
                'conditions': ['is_poacher', 'is_attacking'],
                'description': '박스 안에서 기회를 노려 슈팅하는 공격수'
            },
            'Complete Forward': {
                'conditions': ['is_attacking', 'is_playmaker', 'is_target_man'],
                'description': '공격, 연계, 슈팅 모두를 수행하는 완전한 공격수'
            },
        },
        'RW': {
            'Winger': {
                'conditions': ['is_wide_player', 'is_attacking'],
                'description': '측면에서 돌파와 크로스를 제공하는 윙어'
            },
            'Inside Forward': {
                'conditions': ['is_wide_player', 'is_attacking', 'is_central_player'],
                'description': '측면에서 시작해 중앙으로 침투하는 인사이드 포워드'
            },
            'Wide Playmaker': {
                'conditions': ['is_wide_player', 'is_playmaker'],
                'description': '측면에서 패스로 공격을 조율하는 플레이메이커'
            },
        },
        'LW': {
            'Winger': {
                'conditions': ['is_wide_player', 'is_attacking'],
                'description': '측면에서 돌파와 크로스를 제공하는 윙어'
            },
            'Inside Forward': {
                'conditions': ['is_wide_player', 'is_attacking', 'is_central_player'],
                'description': '측면에서 시작해 중앙으로 침투하는 인사이드 포워드'
            },
            'Wide Playmaker': {
                'conditions': ['is_wide_player', 'is_playmaker'],
                'description': '측면에서 패스로 공격을 조율하는 플레이메이커'
            },
        },
        'LB': {
            'Full-Back': {
                'conditions': ['is_wide_player', 'is_defensive'],
                'description': '측면 수비와 공격 지원을 하는 풀백'
            },
            'Wing-Back': {
                'conditions': ['is_wide_player', 'is_attacking', 'is_defensive'],
                'description': '공격과 수비 모두를 수행하는 윙백'
            },
            'Inverted Wing-Back': {
                'conditions': ['is_wide_player', 'is_central_player', 'is_playmaker'],
                'description': '측면에서 시작해 중앙으로 들어와 빌드업에 참여하는 인벌빙 윙백'
            },
        },
        'RB': {
            'Full-Back': {
                'conditions': ['is_wide_player', 'is_defensive'],
                'description': '측면 수비와 공격 지원을 하는 풀백'
            },
            'Wing-Back': {
                'conditions': ['is_wide_player', 'is_attacking', 'is_defensive'],
                'description': '공격과 수비 모두를 수행하는 윙백'
            },
            'Inverted Wing-Back': {
                'conditions': ['is_wide_player', 'is_central_player', 'is_playmaker'],
                'description': '측면에서 시작해 중앙으로 들어와 빌드업에 참여하는 인벌빙 윙백'
            },
        },
        'GK': {
            'Sweeper Keeper': {
                'conditions': ['is_ball_playing', 'is_long_passer'],
                'description': '빌드업에 참여하고 롱패스로 공격을 전개하는 스위퍼 키퍼'
            },
            'Goalkeeper': {
                'conditions': [],
                'description': '전형적인 골키퍼'
            },
        },
        'LM': {
            'Wide Midfielder': {
                'conditions': ['is_wide_player', 'is_playmaker'],
                'description': '측면에서 패스로 공격을 조율하는 와이드 미드필더'
            },
            'Winger': {
                'conditions': ['is_wide_player', 'is_attacking'],
                'description': '측면에서 돌파와 크로스를 제공하는 윙어'
            },
            'Central Midfielder': {
                'conditions': ['is_central_player', 'is_playmaker'],
                'description': '중앙에서 활동하는 미드필더'
            },
        },
        'RM': {
            'Wide Midfielder': {
                'conditions': ['is_wide_player', 'is_playmaker'],
                'description': '측면에서 패스로 공격을 조율하는 와이드 미드필더'
            },
            'Winger': {
                'conditions': ['is_wide_player', 'is_attacking'],
                'description': '측면에서 돌파와 크로스를 제공하는 윙어'
            },
            'Central Midfielder': {
                'conditions': ['is_central_player', 'is_playmaker'],
                'description': '중앙에서 활동하는 미드필더'
            },
        },
        'LWB': {
            'Wing-Back': {
                'conditions': ['is_wide_player', 'is_attacking', 'is_defensive'],
                'description': '공격과 수비 모두를 수행하는 윙백'
            },
            'Full-Back': {
                'conditions': ['is_wide_player', 'is_defensive'],
                'description': '측면 수비와 공격 지원을 하는 풀백'
            },
            'Inverted Wing-Back': {
                'conditions': ['is_wide_player', 'is_central_player', 'is_playmaker'],
                'description': '측면에서 시작해 중앙으로 들어와 빌드업에 참여하는 인벌빙 윙백'
            },
        },
        'RWB': {
            'Wing-Back': {
                'conditions': ['is_wide_player', 'is_attacking', 'is_defensive'],
                'description': '공격과 수비 모두를 수행하는 윙백'
            },
            'Full-Back': {
                'conditions': ['is_wide_player', 'is_defensive'],
                'description': '측면 수비와 공격 지원을 하는 풀백'
            },
            'Inverted Wing-Back': {
                'conditions': ['is_wide_player', 'is_central_player', 'is_playmaker'],
                'description': '측면에서 시작해 중앙으로 들어와 빌드업에 참여하는 인벌빙 윙백'
            },
        },
    }
    
    if position not in fm_roles:
        return None, "포지션에 대한 FM 롤 정의 없음"
    
    # 조건 매칭 점수 계산
    candidates = []
    
    for role_name, role_info in fm_roles[position].items():
        conditions = role_info['conditions']
        priority = role_info.get('priority', 999)  # 우선순위 (낮을수록 높음)
        
        if len(conditions) == 0:
            # 기본 롤 (조건 없음)
            candidates.append((role_name, role_info['description'], [], 0, priority))
            continue
        
        score = 0
        matched_conditions = []
        for condition in conditions:
            if condition.startswith('not '):
                cond_name = condition[4:]
                if not characteristics.get(cond_name, False):
                    score += 1
                    matched_conditions.append(condition)
            else:
                if characteristics.get(condition, False):
                    score += 1
                    matched_conditions.append(condition)
        
        # 조건 매칭 비율
        match_ratio = score / len(conditions) if len(conditions) > 0 else 0
        
        candidates.append((role_name, role_info['description'], matched_conditions, match_ratio, priority))
    
    # 매칭률이 같으면 우선순위가 높은 것 선택, 우선순위도 같으면 매칭률이 높은 것 선택
    candidates.sort(key=lambda x: (-x[3], x[4]))  # 매칭률 내림차순, 우선순위 오름차순
    
    if candidates:
        best = candidates[0]
        return (best[0], best[1], best[2], best[3])
    
    return None, "매칭 실패"

def assign_role_names(templates):
    """모든 롤에 FM 명칭 부여"""
    print("="*80)
    print("풋볼 매니저 롤 명칭 부여")
    print("="*80)
    print("\n레퍼런스: Football Manager 게임의 포지션별 롤 정의")
    print("방법: 각 클러스터의 특성을 분석하여 가장 적합한 FM 롤과 매칭\n")
    
    named_templates = {}
    
    for position, roles in templates.items():
        print(f"\n{'='*80}")
        print(f"{position} 포지션")
        print(f"{'='*80}")
        
        named_roles = {}
        
        for role_key, template in roles.items():
            characteristics = analyze_role_characteristics(template)
            match_result = match_fm_role(position, template, characteristics)
            
            if match_result and len(match_result) >= 2:
                role_name = match_result[0]
                description = match_result[1]
                
                if len(match_result) > 2:
                    matched_conditions = match_result[2]
                    match_ratio = match_result[3]
                    print(f"\n{role_key} → {role_name} (매칭률: {match_ratio:.1%})")
                    print(f"  설명: {description}")
                    print(f"  매칭된 특성: {', '.join(matched_conditions)}")
                else:
                    print(f"\n{role_key} → {role_name}")
                    print(f"  설명: {description}")
                
                # 주요 지표 출력
                print(f"  주요 지표:")
                print(f"    평균 터치 Y: {template.get('average_touch_y', 0):.1f}")
                print(f"    롱패스 비율: {template.get('long_pass_ratio', 0):.2%}")
                print(f"    짧은 패스 비율: {template.get('short_pass_ratio', 0):.2%}")
                print(f"    패스 성공률: {template.get('pass_success_rate', 0):.2%}")
                print(f"    전진 지역 터치: {template.get('touch_zone_forward', 0):.2%}")
                print(f"    수비 행동 빈도: {template.get('defensive_action_frequency', 0):.2%}")
                
                named_roles[role_name] = {
                    'original_key': role_key,
                    'description': description,
                    'template': template,
                    'characteristics': characteristics
                }
            else:
                print(f"\n{role_key} → 매칭 실패 (기본 이름 유지)")
                named_roles[role_key] = {
                    'original_key': role_key,
                    'description': 'FM 롤 매칭 실패',
                    'template': template,
                    'characteristics': characteristics
                }
        
        named_templates[position] = named_roles
    
    return named_templates

def save_named_templates(named_templates, output_path):
    """명명된 롤 템플릿 저장"""
    # JSON 직렬화를 위해 numpy 타입 변환
    def convert_numpy(obj):
        if isinstance(obj, np.integer):
            return int(obj)
        elif isinstance(obj, np.floating):
            return float(obj)
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        elif isinstance(obj, dict):
            return {k: convert_numpy(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [convert_numpy(item) for item in obj]
        return obj
    
    cleaned = convert_numpy(named_templates)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(cleaned, f, ensure_ascii=False, indent=2)
    
    print(f"\n✓ 명명된 롤 템플릿 저장: {output_path}")

def main():
    templates = load_role_templates()
    
    if templates is None:
        print("❌ 롤 템플릿 파일을 찾을 수 없습니다.")
        print("   먼저 analysis/define_roles_from_data.py를 실행하세요.")
        return
    
    # FM 롤 명칭 부여
    named_templates = assign_role_names(templates)
    
    # 결과 저장
    output_path = PROJECT_ROOT / 'analysis' / 'role_templates_named.json'
    save_named_templates(named_templates, output_path)
    
    print("\n" + "="*80)
    print("롤 명칭 부여 완료")
    print("="*80)
    print("\n각 롤은 다음 기준으로 명명되었습니다:")
    print("1. 실제 데이터 기반 클러스터링 결과")
    print("2. 풋볼 매니저 게임의 롤 정의와 특성 매칭")
    print("3. 각 롤의 행동 프로파일 특성 분석")
    print("\n주의: 매칭률이 낮은 롤은 도메인 전문가 검토가 필요할 수 있습니다.")

if __name__ == '__main__':
    main()


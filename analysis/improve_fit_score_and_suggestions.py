"""
적합도 점수 개선 및 선수 개선 방안 제안 시스템

1. 적합도 점수 개선:
   - 코사인 유사도만 사용하면 점수가 높게 몰림
   - 유클리드 거리 기반 점수 추가
   - 지표별 가중치 적용
   - 포지션 평균 대비 차이 반영

2. 개선 방안 제안:
   - 선수의 약점 지표 식별
   - 상위 선수들과 비교하여 개선점 도출
   - 구체적인 목표 수치 제시
   - 검증 방법 제안
"""

import pandas as pd
import numpy as np
from pathlib import Path
from scipy.spatial.distance import cosine, euclidean
from collections import defaultdict

PROJECT_ROOT = Path(__file__).parent.parent

def calculate_improved_fit_score(player_profile, role_template, position_average=None):
    """
    개선된 적합도 점수 계산
    
    방법:
    1. 코사인 유사도 (방향 유사성)
    2. 유클리드 거리 기반 점수 (크기 차이)
    3. 지표별 가중치 적용
    4. 포지션 평균 대비 차이 반영
    """
    if player_profile is None or role_template is None:
        return None
    
    # 공통 지표 추출
    metrics = [
        'forward_pass_ratio', 'long_pass_ratio', 'very_long_pass_ratio', 'short_pass_ratio',
        'average_pass_length', 'pass_success_rate', 'forward_pass_success_rate',
        'average_forward_pass_distance', 'average_carry_length', 'carry_frequency',
        'average_touch_x', 'average_touch_y', 'touch_zone_central', 'touch_zone_wide',
        'touch_zone_defensive', 'touch_zone_midfield', 'touch_zone_forward',
        'defensive_action_frequency', 'tackle_frequency', 'clearance_frequency',
        'shot_frequency', 'pass_frequency', 'pass_received_frequency'
    ]
    
    # 롤별 중요 지표 가중치 (롤에 따라 다르게 설정 가능)
    weights = {
        'Deep Lying Playmaker': {
            'long_pass_ratio': 1.5,
            'very_long_pass_ratio': 1.5,
            'pass_success_rate': 1.5,
            'touch_zone_central': 1.3,
            'average_touch_y': 1.3,  # 후방 위치
        },
        'Ball Playing Defender': {
            'long_pass_ratio': 1.5,
            'pass_success_rate': 1.5,
            'pass_frequency': 1.3,
        },
        'Poacher': {
            'shot_frequency': 2.0,
            'touch_zone_forward': 1.5,
        },
        # 기본 가중치 (모든 지표 1.0)
    }
    
    player_vector = np.array([player_profile.get(m, 0) for m in metrics])
    role_vector = np.array([role_template.get(m, 0) for m in metrics])
    
    # 1. 코사인 유사도 (방향 유사성)
    player_norm = player_vector / (np.linalg.norm(player_vector) + 1e-10)
    role_norm = role_vector / (np.linalg.norm(role_vector) + 1e-10)
    cosine_sim = 1 - cosine(player_norm, role_norm)
    
    # 2. 유클리드 거리 기반 점수 (크기 차이)
    # 각 지표를 0~1 범위로 정규화 (최대값 기준)
    max_values = np.maximum(player_vector, role_vector)
    max_values = np.maximum(max_values, 1.0)  # 최소 1.0
    
    player_normalized = player_vector / max_values
    role_normalized = role_vector / max_values
    
    # 유클리드 거리 (0~1 범위로 정규화)
    euclidean_dist = euclidean(player_normalized, role_normalized)
    max_possible_dist = np.sqrt(len(metrics))  # 최대 가능한 거리
    euclidean_score = 1 - (euclidean_dist / max_possible_dist)
    euclidean_score = max(0, min(1, euclidean_score))  # 0~1 범위로 클리핑
    
    # 3. 가중 평균 (코사인 60%, 유클리드 40%)
    combined_score = 0.6 * cosine_sim + 0.4 * euclidean_score
    
    # 4. 포지션 평균 대비 차이 반영 (선택적)
    if position_average is not None:
        avg_vector = np.array([position_average.get(m, 0) for m in metrics])
        # 롤 템플릿이 포지션 평균과 얼마나 다른지
        role_deviation = euclidean(role_normalized, avg_vector / max_values) / max_possible_dist
        # 선수가 롤에 가까우면서도 포지션 평균과는 다른 정도
        bonus = role_deviation * 0.1  # 최대 10% 보너스
        combined_score = min(1.0, combined_score + bonus)
    
    # 100점 만점으로 변환
    final_score = combined_score * 100
    
    return {
        'fit_score': final_score,
        'cosine_score': cosine_sim * 100,
        'euclidean_score': euclidean_score * 100,
        'raw_cosine': cosine_sim,
        'raw_euclidean': euclidean_score
    }

def identify_weaknesses(player_profile, role_template, top_players_profiles):
    """
    선수의 약점 지표 식별
    
    방법:
    1. 롤 템플릿과의 차이
    2. 상위 선수들과의 차이
    3. 중요 지표 우선
    """
    if player_profile is None or role_template is None:
        return []
    
    metrics = [
        'forward_pass_ratio', 'long_pass_ratio', 'very_long_pass_ratio', 'short_pass_ratio',
        'average_pass_length', 'pass_success_rate', 'forward_pass_success_rate',
        'average_forward_pass_distance', 'average_carry_length', 'carry_frequency',
        'average_touch_x', 'average_touch_y', 'touch_zone_central', 'touch_zone_wide',
        'touch_zone_defensive', 'touch_zone_midfield', 'touch_zone_forward',
        'defensive_action_frequency', 'tackle_frequency', 'clearance_frequency',
        'shot_frequency', 'pass_frequency', 'pass_received_frequency'
    ]
    
    weaknesses = []
    
    # 롤 템플릿과의 차이
    for metric in metrics:
        player_value = player_profile.get(metric, 0)
        template_value = role_template.get(metric, 0)
        
        if template_value == 0:
            continue
        
        # 차이 비율
        if template_value > 0:
            diff_ratio = abs(player_value - template_value) / template_value
        else:
            diff_ratio = abs(player_value - template_value)
        
        # 상위 선수들의 평균
        top_avg = np.mean([p.get(metric, 0) for p in top_players_profiles if p is not None])
        
        # 중요도 계산 (템플릿과의 차이 + 상위 선수와의 차이)
        importance = diff_ratio * 0.6 + (abs(player_value - top_avg) / (top_avg + 1e-10)) * 0.4
        
        if importance > 0.1:  # 10% 이상 차이
            weaknesses.append({
                'metric': metric,
                'player_value': player_value,
                'template_value': template_value,
                'top_avg': top_avg,
                'gap': player_value - template_value,
                'importance': importance,
                'direction': 'increase' if player_value < template_value else 'decrease'
            })
    
    # 중요도 순으로 정렬
    weaknesses.sort(key=lambda x: x['importance'], reverse=True)
    
    return weaknesses[:5]  # 상위 5개만

def suggest_improvements(player_profile, role_template, top_players_profiles, position_average):
    """
    선수 개선 방안 제안
    
    반환:
    - 약점 지표 목록
    - 구체적인 목표 수치
    - 우선순위
    - 검증 방법
    """
    weaknesses = identify_weaknesses(player_profile, role_template, top_players_profiles)
    
    suggestions = []
    
    for weakness in weaknesses:
        metric = weakness['metric']
        current = weakness['player_value']
        target = weakness['template_value']
        top_avg = weakness['top_avg']
        
        # 목표 수치 (템플릿과 상위 선수 평균의 중간값)
        goal = (target * 0.6 + top_avg * 0.4)
        
        # 개선 필요량
        improvement_needed = goal - current
        
        # 지표 이름 한글화
        metric_names = {
            'forward_pass_ratio': '전방 패스 비율',
            'long_pass_ratio': '롱패스 비율',
            'pass_success_rate': '패스 성공률',
            'touch_zone_central': '중앙 지역 터치 비율',
            'average_touch_y': '평균 터치 Y 위치',
            'shot_frequency': '슈팅 빈도',
            'defensive_action_frequency': '수비 행동 빈도',
        }
        
        metric_name = metric_names.get(metric, metric)
        
        suggestions.append({
            'metric': metric,
            'metric_name': metric_name,
            'current': current,
            'target': target,
            'goal': goal,
            'improvement_needed': improvement_needed,
            'priority': weakness['importance'],
            'direction': weakness['direction']
        })
    
    return suggestions

def validate_improvement(player_id, metric, before_value, after_value, goal_value):
    """
    개선 검증
    
    반환:
    - 개선 여부
    - 목표 달성 여부
    - 개선 정도
    """
    improvement = after_value - before_value
    goal_achieved = abs(after_value - goal_value) < abs(before_value - goal_value)
    improvement_ratio = improvement / abs(goal_value - before_value) if abs(goal_value - before_value) > 0 else 0
    
    return {
        'improved': improvement > 0 if goal_value > before_value else improvement < 0,
        'goal_achieved': goal_achieved,
        'improvement': improvement,
        'improvement_ratio': improvement_ratio
    }

if __name__ == '__main__':
    print("적합도 점수 개선 및 개선 방안 제안 시스템")
    print("="*80)


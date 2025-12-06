"""
팀별 개선점 분석 및 보완 선수 추천

목적:
1. 각 팀의 포지션별/역할별 약점 파악
2. 다른 팀 선수 중 보완 가능한 선수 추천
3. 추천 이유 제공
"""

import pandas as pd
import numpy as np
import json
from pathlib import Path
from collections import defaultdict

PROJECT_ROOT = Path(__file__).parent.parent

def load_data():
    """데이터 로딩"""
    df = pd.read_csv(PROJECT_ROOT / 'raw_data' / 'open_track2' / 'raw_data.csv')
    match_info_df = pd.read_csv(PROJECT_ROOT / 'raw_data' / 'open_track2' / 'match_info.csv')
    return df, match_info_df

def load_role_templates():
    """롤 템플릿 로딩"""
    template_path = PROJECT_ROOT / 'analysis' / 'role_templates_named.json'
    with open(template_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def load_teams_data():
    """팀 데이터 로딩"""
    data_path = PROJECT_ROOT / 'docs' / 'data' / 'teams_data_enhanced.json'
    with open(data_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def analyze_team_weaknesses(team_data):
    """팀의 약점 분석"""
    weaknesses = {
        'position_coverage': {},  # 포지션별 커버리지
        'role_coverage': {},      # 역할별 커버리지
        'quality_gaps': []        # 품질 격차
    }
    
    # 포지션별 선수 수 및 평균 점수
    position_stats = defaultdict(lambda: {'count': 0, 'total_score': 0, 'players': []})
    
    for player in team_data.get('players', []):
        position = player.get('position')
        fit_score = player.get('fit_score', 0)
        
        if position:
            position_stats[position]['count'] += 1
            position_stats[position]['total_score'] += fit_score
            position_stats[position]['players'].append({
                'name': player.get('player_name'),
                'score': fit_score,
                'role': player.get('role')
            })
    
    # 포지션별 평균 점수 계산
    for position, stats in position_stats.items():
        avg_score = stats['total_score'] / stats['count'] if stats['count'] > 0 else 0
        weaknesses['position_coverage'][position] = {
            'count': stats['count'],
            'average_score': round(avg_score, 1),
            'players': stats['players']
        }
    
    # 역할별 커버리지 분석
    role_coverage = defaultdict(lambda: {'count': 0, 'max_score': 0})
    for player in team_data.get('players', []):
        role = player.get('role')
        fit_score = player.get('fit_score', 0)
        if role:
            role_coverage[role]['count'] += 1
            role_coverage[role]['max_score'] = max(role_coverage[role]['max_score'], fit_score)
    
    weaknesses['role_coverage'] = {
        role: {
            'count': stats['count'],
            'max_score': round(stats['max_score'], 1)
        }
        for role, stats in role_coverage.items()
    }
    
    # 품질 격차 분석 (낮은 점수의 포지션/역할)
    for position, stats in weaknesses['position_coverage'].items():
        if stats['average_score'] < 70:  # 평균 점수가 70 미만인 경우
            weaknesses['quality_gaps'].append({
                'type': 'position',
                'position': position,
                'average_score': stats['average_score'],
                'count': stats['count'],
                'reason': f'{position} 포지션의 평균 적합도 점수가 낮습니다 ({stats["average_score"]}점)'
            })
    
    return weaknesses

def find_recommended_players(target_team_data, all_teams_data, target_team_name):
    """보완 가능한 선수 추천"""
    recommendations = []
    
    # 타겟 팀의 약점 분석
    weaknesses = analyze_team_weaknesses(target_team_data)
    
    # 다른 팀들의 선수 데이터 수집
    all_players = []
    for team_name, team_data in all_teams_data.items():
        if team_name == target_team_name:
            continue
        
        for player in team_data.get('players', []):
            all_players.append({
                'player_id': player.get('player_id'),
                'player_name': player.get('player_name'),
                'position': player.get('position'),
                'role': player.get('role'),
                'fit_score': player.get('fit_score', 0),
                'team_name': team_name,
                'game_count': player.get('game_count', 0),
                'team_win_rate': player.get('team_win_rate', 0.5)
            })
    
    # 포지션별 약점 보완
    for gap in weaknesses['quality_gaps']:
        if gap['type'] == 'position':
            position = gap['position']
            target_score = gap['average_score']
            
            # 해당 포지션의 다른 팀 선수 중 높은 점수 선수 찾기
            position_players = [p for p in all_players if p['position'] == position]
            position_players.sort(key=lambda x: x['fit_score'], reverse=True)
            
            # 타겟 팀보다 높은 점수의 선수들 추천
            recommended = []
            for player in position_players[:10]:  # 상위 10명
                if player['fit_score'] > target_score + 5:  # 최소 5점 이상 높아야 함
                    reason = f"{position} 포지션에서 타겟 팀 평균({target_score}점)보다 {player['fit_score'] - target_score:.1f}점 높은 성능을 보입니다"
                    recommended.append({
                        'player_id': player['player_id'],
                        'player_name': player['player_name'],
                        'position': position,
                        'role': player['role'],
                        'fit_score': round(player['fit_score'], 1),
                        'team_name': player['team_name'],
                        'game_count': player['game_count'],
                        'team_win_rate': round(player['team_win_rate'], 3),
                        'reason': reason,
                        'improvement_potential': round(player['fit_score'] - target_score, 1)
                    })
            
            if recommended:
                recommendations.append({
                    'gap_type': 'position',
                    'position': position,
                    'current_average': target_score,
                    'recommended_players': recommended[:5]  # 상위 5명만
                })
    
    # 역할별 약점 보완
    for role, stats in weaknesses['role_coverage'].items():
        if stats['count'] == 0:  # 해당 역할의 선수가 없는 경우
            # 해당 역할을 가진 다른 팀 선수 찾기
            role_players = [p for p in all_players if p['role'] == role]
            role_players.sort(key=lambda x: x['fit_score'], reverse=True)
            
            if role_players:
                recommended = []
                for player in role_players[:5]:
                    reason = f"{role} 역할의 선수가 팀에 없어 보완이 필요합니다. 이 선수는 {player['fit_score']:.1f}점의 높은 적합도를 보입니다"
                    recommended.append({
                        'player_id': player['player_id'],
                        'player_name': player['player_name'],
                        'position': player['position'],
                        'role': role,
                        'fit_score': round(player['fit_score'], 1),
                        'team_name': player['team_name'],
                        'game_count': player['game_count'],
                        'team_win_rate': round(player['team_win_rate'], 3),
                        'reason': reason,
                        'improvement_potential': round(player['fit_score'], 1)
                    })
                
                recommendations.append({
                    'gap_type': 'role',
                    'role': role,
                    'current_count': 0,
                    'recommended_players': recommended
                })
        elif stats['max_score'] < 75:  # 최고 점수가 75 미만인 경우
            role_players = [p for p in all_players if p['role'] == role]
            role_players.sort(key=lambda x: x['fit_score'], reverse=True)
            
            recommended = []
            for player in role_players[:5]:
                if player['fit_score'] > stats['max_score'] + 5:
                    reason = f"{role} 역할에서 팀 최고 점수({stats['max_score']}점)보다 {player['fit_score'] - stats['max_score']:.1f}점 높은 성능을 보입니다"
                    recommended.append({
                        'player_id': player['player_id'],
                        'player_name': player['player_name'],
                        'position': player['position'],
                        'role': role,
                        'fit_score': round(player['fit_score'], 1),
                        'team_name': player['team_name'],
                        'game_count': player['game_count'],
                        'team_win_rate': round(player['team_win_rate'], 3),
                        'reason': reason,
                        'improvement_potential': round(player['fit_score'] - stats['max_score'], 1)
                    })
            
            if recommended:
                recommendations.append({
                    'gap_type': 'role',
                    'role': role,
                    'current_max_score': stats['max_score'],
                    'recommended_players': recommended
                })
    
    return recommendations, weaknesses

# 포메이션별 포지션 구성 정의
FORMATION_CONFIGS = {
    '4-4-2': {
        'GK': 1,
        'LB': 1, 'CB': 2, 'RB': 1,
        'LM': 1, 'CM': 2, 'RM': 1,
        'ST': 2
    },
    '4-3-3': {
        'GK': 1,
        'LB': 1, 'CB': 2, 'RB': 1,
        'CDM': 1, 'CM': 2,
        'LW': 1, 'ST': 1, 'RW': 1
    },
    '5-3-2': {
        'GK': 1,
        'LWB': 1, 'CB': 3, 'RWB': 1,
        'CM': 3,
        'ST': 2
    },
    '4-3-1-2': {
        'GK': 1,
        'LB': 1, 'CB': 2, 'RB': 1,
        'CM': 3,
        'CAM': 1,
        'ST': 2
    },
    '4-5-1': {
        'GK': 1,
        'LB': 1, 'CB': 2, 'RB': 1,
        'LM': 1, 'CM': 3, 'RM': 1,
        'ST': 1
    }
}

def generate_best_11_for_formation(all_teams_data, formation_name):
    """특정 포메이션에 대한 베스트 11 생성 (중복 방지, 포지션 매핑 및 대체 포지션 지원)"""
    if formation_name not in FORMATION_CONFIGS:
        return {}
    
    position_requirements = FORMATION_CONFIGS[formation_name]
    all_players = []
    
    # 포지션 매핑 (LM/RM -> CM, LWB/RWB -> LB/RB)
    position_mapping = {
        'LM': 'CM',
        'RM': 'CM',
        'LWB': 'LB',
        'RWB': 'RB'
    }
    
    # 포지션 대체 우선순위 (해당 포지션이 없을 때 대체할 포지션)
    position_fallback = {
        'CDM': ['CM', 'CB'],  # CDM이 없으면 CM 또는 CB에서 찾기
        'ST': ['CF', 'CAM'],  # ST가 없으면 CF 또는 CAM에서 찾기
        'CAM': ['CM', 'CF'],  # CAM이 없으면 CM 또는 CF에서 찾기
        'LW': ['LM', 'CM'],   # LW가 없으면 LM 또는 CM에서 찾기
        'RW': ['RM', 'CM'],   # RW가 없으면 RM 또는 CM에서 찾기
        'LM': ['CM', 'LW'],   # LM이 없으면 CM 또는 LW에서 찾기
        'RM': ['CM', 'RW'],   # RM이 없으면 CM 또는 RW에서 찾기
        'LWB': ['LB', 'LM'],  # LWB가 없으면 LB 또는 LM에서 찾기
        'RWB': ['RB', 'RM']   # RWB가 없으면 RB 또는 RM에서 찾기
    }
    
    # 모든 선수 수집
    for team_name, team_data in all_teams_data.items():
        for player in team_data.get('players', []):
            all_players.append({
                'player_id': player.get('player_id'),
                'player_name': player.get('player_name'),
                'position': player.get('position'),
                'role': player.get('role'),
                'fit_score': player.get('fit_score', 0),
                'team_name': team_name,
                'game_count': player.get('game_count', 0),
                'team_win_rate': player.get('team_win_rate', 0.5)
            })
    
    # 선수 중복 방지를 위한 집합
    selected_player_ids = set()
    best_11 = {}
    
    # 포지션별로 최고 선수 선택 (중복 방지, 대체 포지션 지원)
    for position, count in position_requirements.items():
        selected = []
        
        # 1. 정확한 포지션 매칭 시도
        position_players = [
            p for p in all_players 
            if p['position'] == position and p['player_id'] not in selected_player_ids
        ]
        position_players.sort(key=lambda x: x['fit_score'], reverse=True)
        
        # 2. 포지션 매핑 적용 (LM -> CM 등)
        if len(position_players) < count:
            mapped_position = position_mapping.get(position, position)
            mapped_players = [
                p for p in all_players 
                if p['position'] == mapped_position and p['player_id'] not in selected_player_ids
            ]
            mapped_players.sort(key=lambda x: x['fit_score'], reverse=True)
            position_players.extend(mapped_players)
            position_players.sort(key=lambda x: x['fit_score'], reverse=True)
        
        # 3. 대체 포지션 시도 (CDM -> CM, ST -> CF 등)
        if len(position_players) < count and position in position_fallback:
            for fallback_pos in position_fallback[position]:
                fallback_players = [
                    p for p in all_players 
                    if p['position'] == fallback_pos and p['player_id'] not in selected_player_ids
                ]
                fallback_players.sort(key=lambda x: x['fit_score'], reverse=True)
                position_players.extend(fallback_players)
            position_players.sort(key=lambda x: x['fit_score'], reverse=True)
        
        # 중복 제거 (같은 선수가 여러 번 포함될 수 있음)
        seen_ids = set()
        unique_players = []
        for p in position_players:
            if p['player_id'] not in seen_ids:
                seen_ids.add(p['player_id'])
                unique_players.append(p)
        
        # 필요한 수만큼 선수 선택
        for player in unique_players[:count]:
            if player['player_id'] not in selected_player_ids:
                selected_player_ids.add(player['player_id'])
                selected.append({
                    'player_id': player['player_id'],
                    'player_name': player['player_name'],
                    'position': position,  # 원래 포지션 이름 유지 (LM, RM 등)
                    'role': player['role'],
                    'fit_score': round(player['fit_score'], 1),
                    'team_name': player['team_name'],
                    'game_count': player['game_count'],
                    'team_win_rate': round(player['team_win_rate'], 3)
                })
        
        if selected:
            best_11[position] = selected
    
    return best_11

def generate_best_11(all_teams_data):
    """모든 포메이션에 대한 베스트 11 생성"""
    best_11_by_formation = {}
    
    for formation_name in FORMATION_CONFIGS.keys():
        best_11_by_formation[formation_name] = generate_best_11_for_formation(
            all_teams_data, formation_name
        )
    
    return best_11_by_formation

def generate_improvement_data():
    """모든 팀의 개선점 분석 및 베스트 11 생성"""
    print("팀 데이터 로딩 중...")
    all_teams_data = load_teams_data()
    
    print("팀별 개선점 분석 중...")
    team_improvements = {}
    
    for team_name, team_data in all_teams_data.items():
        print(f"  {team_name} 분석 중...")
        recommendations, weaknesses = find_recommended_players(team_data, all_teams_data, team_name)
        team_improvements[team_name] = {
            'weaknesses': weaknesses,
            'recommendations': recommendations
        }
    
    print("베스트 11 생성 중...")
    best_11 = generate_best_11(all_teams_data)
    
    # 결과 저장
    output_data = {
        'team_improvements': team_improvements,
        'best_11': best_11
    }
    
    output_path = PROJECT_ROOT / 'docs' / 'data' / 'team_improvements.json'
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, ensure_ascii=False, indent=2)
    
    print(f"\n결과 저장 완료: {output_path}")
    return output_data

if __name__ == '__main__':
    generate_improvement_data()


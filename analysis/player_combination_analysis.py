"""
선수 간 조합 분석 시스템

1. 패스 네트워크 분석
2. 롤 조합 분석
3. 공간 활용 조합
4. 시너지 효과 분석
"""

import pandas as pd
import numpy as np
import json
from pathlib import Path
from collections import defaultdict
from itertools import combinations

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

def analyze_pass_network(df, team_id, game_id=None):
    """
    팀의 패스 네트워크 분석
    
    반환:
    - 선수 간 패스 연결 매트릭스
    - 패스 성공률
    - 패스 빈도
    """
    if game_id is not None:
        team_data = df[(df['team_id'] == team_id) & (df['game_id'] == game_id)]
    else:
        team_data = df[df['team_id'] == team_id]
    
    # 패스 데이터만 추출
    passes = team_data[team_data['type_name'] == 'Pass'].copy()
    
    if len(passes) == 0:
        return None
    
    # 패스 연결 매트릭스 생성
    pass_network = defaultdict(lambda: {'count': 0, 'successful': 0})
    
    for idx, pass_row in passes.iterrows():
        passer_id = pass_row['player_id']
        
        # 패스를 받은 선수 찾기 (다음 이벤트가 Pass Received인 경우)
        next_events = team_data[
            (team_data['game_id'] == pass_row['game_id']) &
            (team_data['action_id'] > pass_row['action_id']) &
            (team_data['action_id'] <= pass_row['action_id'] + 5)  # 5개 이벤트 내
        ]
        
        received = next_events[next_events['type_name'] == 'Pass Received']
        if len(received) > 0:
            receiver_id = received.iloc[0]['player_id']
            
            if passer_id != receiver_id:  # 자기 자신에게 패스한 경우 제외
                pass_network[(passer_id, receiver_id)]['count'] += 1
                if pass_row['result_name'] == 'Successful':
                    pass_network[(passer_id, receiver_id)]['successful'] += 1
    
    # 선수 목록
    players = team_data['player_id'].unique()
    player_names = {}
    for player_id in players:
        player_data = team_data[team_data['player_id'] == player_id]
        if len(player_data) > 0:
            player_names[player_id] = player_data['player_name_ko'].iloc[0]
    
    # 네트워크 매트릭스 생성
    network_matrix = {}
    for (passer_id, receiver_id), stats in pass_network.items():
        network_matrix[(passer_id, receiver_id)] = {
            'passer_name': player_names.get(passer_id, '알 수 없음'),
            'receiver_name': player_names.get(receiver_id, '알 수 없음'),
            'count': stats['count'],
            'successful': stats['successful'],
            'success_rate': stats['successful'] / stats['count'] if stats['count'] > 0 else 0
        }
    
    return {
        'network_matrix': network_matrix,
        'players': player_names,
        'total_passes': len(passes)
    }

def analyze_role_combinations(df, match_info_df, team_id, role_templates):
    """
    롤 조합 분석
    
    같은 경기에 출전한 선수들의 롤 조합과 그 효과 분석
    """
    # 팀의 모든 경기
    team_games = df[df['team_id'] == team_id]['game_id'].unique()
    
    role_combinations = defaultdict(lambda: {
        'games': [],
        'wins': 0,
        'draws': 0,
        'losses': 0,
        'goals_for': 0,
        'goals_against': 0,
        'players': set()
    })
    
    # 각 경기별로 분석
    for game_id in team_games:
        game_data = df[(df['game_id'] == game_id) & (df['team_id'] == team_id)]
        if len(game_data) == 0:
            continue
        
        # 경기에 출전한 선수들의 롤 추출
        # (간단화: 각 선수의 가장 적합한 롤 사용)
        game_players = game_data['player_id'].unique()
        game_roles = []
        
        for player_id in game_players:
            player_data = game_data[game_data['player_id'] == player_id]
            if len(player_data) == 0:
                continue
            
            position = player_data['main_position'].iloc[0]
            if position in role_templates:
                # 간단히 첫 번째 롤 사용 (실제로는 적합도 계산 필요)
                roles = list(role_templates[position].keys())
                if roles:
                    game_roles.append((player_id, position, roles[0]))
        
        # 롤 조합 생성 (정렬하여 순서 무관하게)
        if len(game_roles) >= 2:
            role_combo = tuple(sorted([(pos, role) for _, pos, role in game_roles]))
            role_combinations[role_combo]['games'].append(game_id)
            role_combinations[role_combo]['players'].update([pid for pid, _, _ in game_roles])
            
            # 경기 결과
            game_info = match_info_df[match_info_df['game_id'] == game_id]
            if len(game_info) > 0:
                is_home = game_info['home_team_id'].iloc[0] == team_id
                home_score = game_info['home_score'].iloc[0]
                away_score = game_info['away_score'].iloc[0]
                
                if is_home:
                    goals_for = home_score
                    goals_against = away_score
                    if home_score > away_score:
                        role_combinations[role_combo]['wins'] += 1
                    elif home_score == away_score:
                        role_combinations[role_combo]['draws'] += 1
                    else:
                        role_combinations[role_combo]['losses'] += 1
                else:
                    goals_for = away_score
                    goals_against = home_score
                    if away_score > home_score:
                        role_combinations[role_combo]['wins'] += 1
                    elif away_score == away_score:
                        role_combinations[role_combo]['draws'] += 1
                    else:
                        role_combinations[role_combo]['losses'] += 1
                
                role_combinations[role_combo]['goals_for'] += goals_for
                role_combinations[role_combo]['goals_against'] += goals_against
    
    # 결과 정리
    results = []
    for role_combo, stats in role_combinations.items():
        game_count = len(stats['games'])
        if game_count > 0:
            win_rate = stats['wins'] / game_count
            avg_goals_for = stats['goals_for'] / game_count
            avg_goals_against = stats['goals_against'] / game_count
            
            results.append({
                'role_combination': role_combo,
                'game_count': game_count,
                'wins': stats['wins'],
                'draws': stats['draws'],
                'losses': stats['losses'],
                'win_rate': win_rate,
                'avg_goals_for': avg_goals_for,
                'avg_goals_against': avg_goals_against,
                'goal_difference': avg_goals_for - avg_goals_against,
                'player_count': len(stats['players'])
            })
    
    # 승률 순으로 정렬
    results.sort(key=lambda x: x['win_rate'], reverse=True)
    
    return results

def analyze_player_synergy(df, match_info_df, player_id_1, player_id_2):
    """
    두 선수 간의 시너지 효과 분석
    
    두 선수가 함께 뛴 경기 vs 따로 뛴 경기의 성과 비교
    """
    # 선수 1의 경기
    player1_games = set(df[df['player_id'] == player_id_1]['game_id'].unique())
    # 선수 2의 경기
    player2_games = set(df[df['player_id'] == player_id_2]['game_id'].unique())
    
    # 함께 뛴 경기
    together_games = player1_games & player2_games
    # 따로 뛴 경기
    separate_games = (player1_games | player2_games) - together_games
    
    if len(together_games) == 0:
        return None
    
    # 함께 뛴 경기의 성과
    together_stats = calculate_game_performance(match_info_df, together_games, df, player_id_1)
    # 따로 뛴 경기의 성과
    separate_stats = calculate_game_performance(match_info_df, separate_games, df, player_id_1)
    
    return {
        'together_games': len(together_games),
        'separate_games': len(separate_games),
        'together_stats': together_stats,
        'separate_stats': separate_stats,
        'synergy_effect': {
            'win_rate_diff': together_stats['win_rate'] - separate_stats['win_rate'],
            'goals_for_diff': together_stats['avg_goals_for'] - separate_stats['avg_goals_for'],
            'goals_against_diff': together_stats['avg_goals_against'] - separate_stats['avg_goals_against']
        }
    }

def calculate_game_performance(match_info_df, game_ids, df, player_id):
    """경기들의 성과 계산"""
    if len(game_ids) == 0:
        return {
            'win_rate': 0,
            'avg_goals_for': 0,
            'avg_goals_against': 0
        }
    
    wins = 0
    draws = 0
    losses = 0
    goals_for = 0
    goals_against = 0
    
    for game_id in game_ids:
        game_info = match_info_df[match_info_df['game_id'] == game_id]
        if len(game_info) == 0:
            continue
        
        # 선수의 팀 찾기
        player_data = df[(df['game_id'] == game_id) & (df['player_id'] == player_id)]
        if len(player_data) == 0:
            continue
        
        team_id = player_data['team_id'].iloc[0]
        is_home = game_info['home_team_id'].iloc[0] == team_id
        home_score = game_info['home_score'].iloc[0]
        away_score = game_info['away_score'].iloc[0]
        
        if is_home:
            goals_for += home_score
            goals_against += away_score
            if home_score > away_score:
                wins += 1
            elif home_score == away_score:
                draws += 1
            else:
                losses += 1
        else:
            goals_for += away_score
            goals_against += home_score
            if away_score > home_score:
                wins += 1
            elif away_score == home_score:
                draws += 1
            else:
                losses += 1
    
    game_count = len(game_ids)
    return {
        'win_rate': wins / game_count if game_count > 0 else 0,
        'avg_goals_for': goals_for / game_count if game_count > 0 else 0,
        'avg_goals_against': goals_against / game_count if game_count > 0 else 0
    }

def analyze_spatial_coverage(df, team_id, game_id=None):
    """
    공간 활용 조합 분석
    
    선수들의 평균 위치와 공간 커버리지 분석
    """
    if game_id is not None:
        team_data = df[(df['team_id'] == team_id) & (df['game_id'] == game_id)]
    else:
        team_data = df[df['team_id'] == team_id]
    
    # 각 선수의 평균 터치 위치
    player_positions = {}
    touches = team_data[team_data['type_name'].isin(['Pass', 'Carry', 'Shot', 'Pass Received'])]
    
    for player_id in touches['player_id'].unique():
        player_touches = touches[touches['player_id'] == player_id]
        if len(player_touches) > 0:
            player_name = player_touches['player_name_ko'].iloc[0]
            player_positions[player_id] = {
                'name': player_name,
                'avg_x': player_touches['start_x'].mean(),
                'avg_y': player_touches['start_y'].mean(),
                'touch_count': len(player_touches)
            }
    
    # 공간 커버리지 계산 (간단한 방법: 선수들의 위치 분산)
    if len(player_positions) > 0:
        x_positions = [p['avg_x'] for p in player_positions.values()]
        y_positions = [p['avg_y'] for p in player_positions.values()]
        
        spatial_coverage = {
            'x_variance': np.var(x_positions),
            'y_variance': np.var(y_positions),
            'total_variance': np.var(x_positions) + np.var(y_positions),
            'player_positions': player_positions
        }
    else:
        spatial_coverage = None
    
    return spatial_coverage

if __name__ == '__main__':
    print("선수 간 조합 분석 시스템")
    print("="*80)
    
    df, match_info_df = load_data()
    role_templates = load_role_templates()
    
    # 전북 현대 모터스 team_id
    jeonbuk_teams = df[df['team_name_ko'].str.contains('전북', na=False)]
    if len(jeonbuk_teams) > 0:
        jeonbuk_team_id = jeonbuk_teams['team_id'].iloc[0]
        print(f"\n전북 현대 모터스 team_id: {jeonbuk_team_id}")
        
        # 패스 네트워크 분석
        print("\n[1. 패스 네트워크 분석]")
        pass_network = analyze_pass_network(df, jeonbuk_team_id)
        if pass_network:
            print(f"  총 패스 수: {pass_network['total_passes']}")
            print(f"  연결된 선수 쌍: {len(pass_network['network_matrix'])}")
            
            # 상위 10개 패스 연결
            sorted_connections = sorted(
                pass_network['network_matrix'].items(),
                key=lambda x: x[1]['count'],
                reverse=True
            )[:10]
            
            print("\n  상위 10개 패스 연결:")
            for (passer_id, receiver_id), stats in sorted_connections:
                print(f"    {stats['passer_name']} → {stats['receiver_name']}: {stats['count']}회 (성공률: {stats['success_rate']:.1%})")
        
        # 롤 조합 분석
        print("\n[2. 롤 조합 분석]")
        role_combos = analyze_role_combinations(df, match_info_df, jeonbuk_team_id, role_templates)
        print(f"  발견된 롤 조합 수: {len(role_combos)}")
        
        if role_combos:
            print("\n  상위 5개 롤 조합 (승률 기준):")
            for i, combo in enumerate(role_combos[:5], 1):
                print(f"    {i}. {combo['role_combination']}")
                print(f"       경기 수: {combo['game_count']}, 승률: {combo['win_rate']:.1%}")
                print(f"       평균 득점: {combo['avg_goals_for']:.2f}, 평균 실점: {combo['avg_goals_against']:.2f}")


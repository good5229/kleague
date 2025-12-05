"""
전북 현대 모터스 팀 선수 조합 분석 리포트 생성

1. 패스 네트워크 분석
2. 롤 조합 효과 분석
3. 선수 간 시너지 효과 분석
4. 공간 활용 조합 분석
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

def get_player_roles(df, match_info_df, team_id, role_templates):
    """각 선수의 롤 할당 (간단 버전 - 실제로는 jeonbuk_team_analysis.py의 결과 사용)"""
    # 실제로는 jeonbuk_team_analysis.py에서 계산한 롤을 사용해야 함
    # 여기서는 간단히 포지션별 첫 번째 롤 사용
    player_roles = {}
    
    team_players = df[df['team_id'] == team_id].groupby(['player_id', 'player_name_ko', 'main_position']).size().reset_index(name='count')
    
    for _, row in team_players.iterrows():
        player_id = row['player_id']
        position = row['main_position']
        if position in role_templates:
            roles = list(role_templates[position].keys())
            if roles:
                player_roles[player_id] = {
                    'name': row['player_name_ko'],
                    'position': position,
                    'role': roles[0]  # 간단히 첫 번째 롤 사용
                }
    
    return player_roles

def analyze_pass_network_detailed(df, team_id):
    """상세 패스 네트워크 분석"""
    team_data = df[df['team_id'] == team_id]
    passes = team_data[team_data['type_name'] == 'Pass'].copy()
    
    if len(passes) == 0:
        return None
    
    # 패스 연결 추적
    pass_connections = defaultdict(lambda: {'count': 0, 'successful': 0, 'total_length': 0})
    
    for idx, pass_row in passes.iterrows():
        passer_id = pass_row['player_id']
        
        # 패스를 받은 선수 찾기
        next_events = team_data[
            (team_data['game_id'] == pass_row['game_id']) &
            (team_data['action_id'] > pass_row['action_id']) &
            (team_data['action_id'] <= pass_row['action_id'] + 5)
        ]
        
        received = next_events[next_events['type_name'] == 'Pass Received']
        if len(received) > 0:
            receiver_id = received.iloc[0]['player_id']
            
            if passer_id != receiver_id:
                pass_length = np.sqrt(
                    (pass_row['end_x'] - pass_row['start_x'])**2 + 
                    (pass_row['end_y'] - pass_row['start_y'])**2
                )
                
                pass_connections[(passer_id, receiver_id)]['count'] += 1
                pass_connections[(passer_id, receiver_id)]['total_length'] += pass_length
                if pass_row['result_name'] == 'Successful':
                    pass_connections[(passer_id, receiver_id)]['successful'] += 1
    
    # 선수 이름 매핑
    player_names = {}
    for player_id in team_data['player_id'].unique():
        player_data = team_data[team_data['player_id'] == player_id]
        if len(player_data) > 0:
            player_names[player_id] = player_data['player_name_ko'].iloc[0]
    
    # 결과 정리
    connections = []
    for (passer_id, receiver_id), stats in pass_connections.items():
        if stats['count'] >= 10:  # 최소 10회 이상 패스
            connections.append({
                'passer_id': passer_id,
                'passer_name': player_names.get(passer_id, '알 수 없음'),
                'receiver_id': receiver_id,
                'receiver_name': player_names.get(receiver_id, '알 수 없음'),
                'count': stats['count'],
                'successful': stats['successful'],
                'success_rate': stats['successful'] / stats['count'] if stats['count'] > 0 else 0,
                'avg_length': stats['total_length'] / stats['count'] if stats['count'] > 0 else 0
            })
    
    connections.sort(key=lambda x: x['count'], reverse=True)
    
    return connections

def analyze_role_combination_performance(df, match_info_df, team_id, player_roles):
    """롤 조합별 성과 분석"""
    team_games = df[df['team_id'] == team_id]['game_id'].unique()
    
    role_combo_stats = defaultdict(lambda: {
        'games': [],
        'wins': 0,
        'draws': 0,
        'losses': 0,
        'goals_for': 0,
        'goals_against': 0
    })
    
    for game_id in team_games:
        game_data = df[(df['game_id'] == game_id) & (df['team_id'] == team_id)]
        if len(game_data) == 0:
            continue
        
        # 경기 출전 선수들의 롤 조합
        game_player_ids = game_data['player_id'].unique()
        game_roles = []
        
        for player_id in game_player_ids:
            if player_id in player_roles:
                role_info = player_roles[player_id]
                game_roles.append((role_info['position'], role_info['role']))
        
        if len(game_roles) >= 10:  # 최소 10명 이상 출전
            # 롤 조합을 정렬하여 순서 무관하게
            role_combo = tuple(sorted(set(game_roles)))  # 중복 제거
            
            role_combo_stats[role_combo]['games'].append(game_id)
            
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
                        role_combo_stats[role_combo]['wins'] += 1
                    elif home_score == away_score:
                        role_combo_stats[role_combo]['draws'] += 1
                    else:
                        role_combo_stats[role_combo]['losses'] += 1
                else:
                    goals_for = away_score
                    goals_against = home_score
                    if away_score > home_score:
                        role_combo_stats[role_combo]['wins'] += 1
                    elif away_score == home_score:
                        role_combo_stats[role_combo]['draws'] += 1
                    else:
                        role_combo_stats[role_combo]['losses'] += 1
                
                role_combo_stats[role_combo]['goals_for'] += goals_for
                role_combo_stats[role_combo]['goals_against'] += goals_against
    
    # 결과 정리
    results = []
    for role_combo, stats in role_combo_stats.items():
        game_count = len(stats['games'])
        if game_count >= 2:  # 최소 2경기 이상
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
                'goal_difference': avg_goals_for - avg_goals_against
            })
    
    results.sort(key=lambda x: (x['win_rate'], x['goal_difference']), reverse=True)
    return results

def analyze_player_synergy_pairs(df, match_info_df, team_id, min_games_together=3):
    """선수 쌍별 시너지 효과 분석"""
    team_data = df[df['team_id'] == team_id]
    team_players = team_data['player_id'].unique()
    
    # 각 선수의 경기 목록 (NaN 제외)
    player_games = {}
    for player_id in team_players:
        if pd.notna(player_id):
            player_games[player_id] = set(team_data[team_data['player_id'] == player_id]['game_id'].unique())
    
    # 선수 쌍별 시너지 분석
    synergy_results = []
    
    # NaN 제외한 선수 목록
    valid_players = [pid for pid in team_players if pd.notna(pid)]
    
    for player1_id, player2_id in combinations(valid_players, 2):
        if player1_id == player2_id:
            continue
        
        together_games = player_games[player1_id] & player_games[player2_id]
        
        if len(together_games) >= min_games_together:
            # 함께 뛴 경기의 성과
            together_performance = calculate_team_performance(match_info_df, together_games, team_id)
            
            # 각자 따로 뛴 경기
            player1_alone = player_games[player1_id] - player_games[player2_id]
            player2_alone = player_games[player2_id] - player_games[player1_id]
            separate_games = player1_alone | player2_alone
            
            if len(separate_games) > 0:
                separate_performance = calculate_team_performance(match_info_df, separate_games, team_id)
                
                # 선수 이름
                player1_data = team_data[team_data['player_id'] == player1_id]
                player2_data = team_data[team_data['player_id'] == player2_id]
                player1_name = player1_data['player_name_ko'].iloc[0] if len(player1_data) > 0 else '알 수 없음'
                player2_name = player2_data['player_name_ko'].iloc[0] if len(player2_data) > 0 else '알 수 없음'
                
                synergy_results.append({
                    'player1_id': player1_id,
                    'player1_name': player1_name,
                    'player2_id': player2_id,
                    'player2_name': player2_name,
                    'together_games': len(together_games),
                    'separate_games': len(separate_games),
                    'together_win_rate': together_performance['win_rate'],
                    'separate_win_rate': separate_performance['win_rate'],
                    'win_rate_improvement': together_performance['win_rate'] - separate_performance['win_rate'],
                    'together_avg_goals_for': together_performance['avg_goals_for'],
                    'separate_avg_goals_for': separate_performance['avg_goals_for'],
                    'goals_improvement': together_performance['avg_goals_for'] - separate_performance['avg_goals_for']
                })
    
    # 시너지 효과가 큰 순으로 정렬
    synergy_results.sort(key=lambda x: x['win_rate_improvement'], reverse=True)
    
    return synergy_results

def calculate_team_performance(match_info_df, game_ids, team_id):
    """팀의 경기 성과 계산"""
    if len(game_ids) == 0:
        return {'win_rate': 0, 'avg_goals_for': 0, 'avg_goals_against': 0}
    
    wins = 0
    draws = 0
    losses = 0
    goals_for = 0
    goals_against = 0
    
    for game_id in game_ids:
        game_info = match_info_df[match_info_df['game_id'] == game_id]
        if len(game_info) == 0:
            continue
        
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

def generate_combination_report(df, match_info_df, team_id, team_name):
    """선수 조합 분석 리포트 생성"""
    role_templates = load_role_templates()
    player_roles = get_player_roles(df, match_info_df, team_id, role_templates)
    
    md_content = []
    
    md_content.append(f"# {team_name} 선수 조합 분석 리포트")
    md_content.append("")
    md_content.append("## 개요")
    md_content.append("")
    md_content.append("이 리포트는 팀의 선수 간 조합과 시너지 효과를 분석합니다.")
    md_content.append("")
    
    # 1. 패스 네트워크 분석
    md_content.append("## 1. 패스 네트워크 분석")
    md_content.append("")
    md_content.append("선수 간 패스 연결 패턴과 핵심 연결 선수 식별")
    md_content.append("")
    
    pass_network = analyze_pass_network_detailed(df, team_id)
    if pass_network:
        md_content.append("### 상위 패스 연결 (20개)")
        md_content.append("")
        md_content.append("| 순위 | 패스 주는 선수 | 패스를 받는 선수 | 패스 수 | 성공률 | 평균 거리 |")
        md_content.append("|------|---------------|---------------|--------|--------|----------|")
        for i, conn in enumerate(pass_network[:20], 1):
            md_content.append(f"| {i} | {conn['passer_name']} | {conn['receiver_name']} | {conn['count']}회 | {conn['success_rate']:.1%} | {conn['avg_length']:.1f}m |")
        md_content.append("")
        
        # 핵심 연결 선수 (가장 많은 패스를 주고받는 선수)
        player_centrality = defaultdict(lambda: {'out': 0, 'in': 0})
        for conn in pass_network:
            player_centrality[conn['passer_id']]['out'] += conn['count']
            player_centrality[conn['receiver_id']]['in'] += conn['count']
        
        centrality_scores = []
        for player_id, stats in player_centrality.items():
            player_name = pass_network[0]['passer_name'] if pass_network else '알 수 없음'
            for conn in pass_network:
                if conn['passer_id'] == player_id or conn['receiver_id'] == player_id:
                    player_name = conn['passer_name'] if conn['passer_id'] == player_id else conn['receiver_name']
                    break
            
            total = stats['out'] + stats['in']
            centrality_scores.append({
                'player_id': player_id,
                'player_name': player_name,
                'out_passes': stats['out'],
                'in_passes': stats['in'],
                'total': total
            })
        
        centrality_scores.sort(key=lambda x: x['total'], reverse=True)
        
        md_content.append("### 핵심 연결 선수 (패스 중심성)")
        md_content.append("")
        md_content.append("| 순위 | 선수명 | 패스 보낸 수 | 패스 받은 수 | 총합 |")
        md_content.append("|------|--------|------------|------------|------|")
        for i, player in enumerate(centrality_scores[:10], 1):
            md_content.append(f"| {i} | {player['player_name']} | {player['out_passes']}회 | {player['in_passes']}회 | {player['total']}회 |")
        md_content.append("")
    
    # 2. 롤 조합 분석
    md_content.append("## 2. 롤 조합 효과 분석")
    md_content.append("")
    md_content.append("특정 롤 조합이 팀 성과에 미치는 영향")
    md_content.append("")
    
    role_combos = analyze_role_combination_performance(df, match_info_df, team_id, player_roles)
    if role_combos:
        md_content.append("### 효과적인 롤 조합 (상위 5개)")
        md_content.append("")
        for i, combo in enumerate(role_combos[:5], 1):
            md_content.append(f"#### 조합 {i}")
            md_content.append("")
            md_content.append(f"- **롤 구성**: {', '.join([f'{pos}-{role}' for pos, role in combo['role_combination']])}")
            md_content.append(f"- **경기 수**: {combo['game_count']}경기")
            md_content.append(f"- **승률**: {combo['win_rate']:.1%} ({combo['wins']}승 {combo['draws']}무 {combo['losses']}패)")
            md_content.append(f"- **평균 득점**: {combo['avg_goals_for']:.2f}골")
            md_content.append(f"- **평균 실점**: {combo['avg_goals_against']:.2f}골")
            md_content.append(f"- **득실차**: {combo['goal_difference']:+.2f}")
            md_content.append("")
    
    # 3. 선수 간 시너지 효과
    md_content.append("## 3. 선수 간 시너지 효과 분석")
    md_content.append("")
    md_content.append("두 선수가 함께 뛸 때의 시너지 효과")
    md_content.append("")
    
    synergy_results = analyze_player_synergy_pairs(df, match_info_df, team_id, min_games_together=3)
    if synergy_results:
        md_content.append("### 최고 시너지 조합 (상위 10개)")
        md_content.append("")
        md_content.append("| 순위 | 선수 1 | 선수 2 | 함께 뛴 경기 | 승률 개선 | 득점 개선 |")
        md_content.append("|------|--------|--------|------------|----------|----------|")
        for i, synergy in enumerate(synergy_results[:10], 1):
            win_improvement = synergy['win_rate_improvement'] * 100
            goal_improvement = synergy['goals_improvement']
            md_content.append(f"| {i} | {synergy['player1_name']} | {synergy['player2_name']} | {synergy['together_games']}경기 | {win_improvement:+.1f}%p | {goal_improvement:+.2f}골 |")
        md_content.append("")
        
        md_content.append("**해석:**")
        md_content.append("- 승률 개선: 두 선수가 함께 뛴 경기의 승률 - 따로 뛴 경기의 승률")
        md_content.append("- 득점 개선: 두 선수가 함께 뛴 경기의 평균 득점 - 따로 뛴 경기의 평균 득점")
        md_content.append("")
    
    return "\n".join(md_content)

if __name__ == '__main__':
    print("="*80)
    print("전북 현대 모터스 선수 조합 분석")
    print("="*80)
    
    df, match_info_df = load_data()
    
    # 전북 현대 모터스 찾기
    jeonbuk_teams = df[df['team_name_ko'].str.contains('전북', na=False)]
    if len(jeonbuk_teams) > 0:
        jeonbuk_team_id = jeonbuk_teams['team_id'].iloc[0]
        jeonbuk_team_name = jeonbuk_teams['team_name_ko'].iloc[0]
        
        print(f"\n팀: {jeonbuk_team_name} (team_id: {jeonbuk_team_id})")
        
        # 리포트 생성
        report = generate_combination_report(df, match_info_df, jeonbuk_team_id, jeonbuk_team_name)
        
        # 파일 저장
        output_path = PROJECT_ROOT / 'analysis' / 'JEONBUK_COMBINATION_ANALYSIS.md'
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(report)
        
        print(f"\n✓ 리포트 저장 완료: {output_path}")
    else:
        print("전북 현대 모터스를 찾을 수 없습니다.")


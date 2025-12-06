"""
모든 팀의 모든 선수 분석 데이터 생성

GitHub Pages 웹 서비스를 위한 JSON 데이터 생성
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

# jeonbuk_team_analysis.py의 함수들을 import하거나 복사
# 간단하게 필요한 함수들을 여기에 포함
def calculate_player_profile(df, player_id, match_info_df):
    """선수 행동 프로파일 계산 (jeonbuk_team_analysis.py에서 복사)"""
    from scipy.spatial.distance import cosine, euclidean
    
    player_data = df[df['player_id'] == player_id].copy()
    
    if len(player_data) == 0:
        return None
    
    game_count = player_data['game_id'].nunique()
    event_count = len(player_data)
    
    # WAR (Wins Above Replacement) 계산
    # 선수가 뛴 경기에서의 팀 승률 vs 선수가 뛰지 않은 경기에서의 팀 승률 비교
    team_win_rate = None
    war = None
    war_games_with = 0
    war_games_without = 0
    
    if match_info_df is not None:
        player_games = player_data['game_id'].unique()
        player_team_id = player_data['team_id'].iloc[0] if len(player_data) > 0 else None
        
        if player_team_id is not None:
            # 선수가 뛴 경기에서의 팀 승률
            wins_with = 0
            games_with = len(player_games)
            
            for game_id in player_games:
                game_info = match_info_df[match_info_df['game_id'] == game_id]
                if len(game_info) > 0:
                    is_home = game_info['home_team_id'].iloc[0] == player_team_id
                    home_score = game_info['home_score'].iloc[0]
                    away_score = game_info['away_score'].iloc[0]
                    
                    if is_home:
                        if home_score > away_score:
                            wins_with += 1
                    else:
                        if away_score > home_score:
                            wins_with += 1
            
            if games_with > 0:
                team_win_rate = wins_with / games_with
            
            # 선수가 뛰지 않은 경기에서의 팀 승률
            # 해당 팀의 모든 경기 찾기
            team_games = match_info_df[
                (match_info_df['home_team_id'] == player_team_id) | 
                (match_info_df['away_team_id'] == player_team_id)
            ]['game_id'].unique()
            
            # 선수가 뛰지 않은 경기
            games_without = [g for g in team_games if g not in player_games]
            wins_without = 0
            games_without_count = len(games_without)
            
            for game_id in games_without:
                game_info = match_info_df[match_info_df['game_id'] == game_id]
                if len(game_info) > 0:
                    is_home = game_info['home_team_id'].iloc[0] == player_team_id
                    home_score = game_info['home_score'].iloc[0]
                    away_score = game_info['away_score'].iloc[0]
                    
                    if is_home:
                        if home_score > away_score:
                            wins_without += 1
                    else:
                        if away_score > home_score:
                            wins_without += 1
            
            # WAR 계산: 선수가 뛴 경기 승률 - 선수가 뛰지 않은 경기 승률
            if games_with > 0 and games_without_count > 0:
                win_rate_with = wins_with / games_with
                win_rate_without = wins_without / games_without_count
                war = win_rate_with - win_rate_without
                war_games_with = games_with
                war_games_without = games_without_count
            elif games_with > 0:
                # 선수가 뛰지 않은 경기가 없으면 (모든 경기 출전) WAR는 0으로 설정
                war = 0.0
                war_games_with = games_with
                war_games_without = 0
    
    # 패스 관련
    passes = player_data[player_data['type_name'] == 'Pass'].copy()
    if len(passes) > 0:
        passes['pass_length'] = np.sqrt(passes['dx']**2 + passes['dy']**2)
        forward_passes = passes[passes['dx'] > 0]
        profile = {
            'forward_pass_ratio': len(forward_passes) / len(passes),
            'long_pass_ratio': (passes['pass_length'] > 20).sum() / len(passes),
            'very_long_pass_ratio': (passes['pass_length'] > 30).sum() / len(passes),
            'short_pass_ratio': (passes['pass_length'] <= 10).sum() / len(passes),
            'average_pass_length': passes['pass_length'].mean(),
            'pass_success_rate': (passes['result_name'] == 'Successful').sum() / len(passes),
            'forward_pass_success_rate': (forward_passes['result_name'] == 'Successful').sum() / len(forward_passes) if len(forward_passes) > 0 else 0,
            'average_forward_pass_distance': forward_passes['pass_length'].mean() if len(forward_passes) > 0 else 0,
        }
    else:
        profile = {
            'forward_pass_ratio': 0, 'long_pass_ratio': 0, 'very_long_pass_ratio': 0,
            'short_pass_ratio': 0, 'average_pass_length': 0, 'pass_success_rate': 0,
            'forward_pass_success_rate': 0, 'average_forward_pass_distance': 0,
        }
    
    # 캐리 관련
    carries = player_data[player_data['type_name'] == 'Carry'].copy()
    if len(carries) > 0:
        carries['carry_length'] = np.sqrt(carries['dx']**2 + carries['dy']**2)
        profile['average_carry_length'] = carries['carry_length'].mean()
        profile['carry_frequency'] = len(carries) / len(player_data)
    else:
        profile['average_carry_length'] = 0
        profile['carry_frequency'] = 0
    
    # 터치 위치
    profile['average_touch_x'] = player_data['start_x'].mean()
    profile['average_touch_y'] = player_data['start_y'].mean()
    profile['touch_zone_central'] = ((player_data['start_x'] >= 30) & (player_data['start_x'] <= 70)).sum() / len(player_data)
    profile['touch_zone_wide'] = ((player_data['start_x'] < 30) | (player_data['start_x'] > 70)).sum() / len(player_data)
    profile['touch_zone_defensive'] = (player_data['start_y'] < 33.3).sum() / len(player_data)
    profile['touch_zone_midfield'] = ((player_data['start_y'] >= 33.3) & (player_data['start_y'] <= 66.6)).sum() / len(player_data)
    profile['touch_zone_forward'] = (player_data['start_y'] > 66.6).sum() / len(player_data)
    
    # 수비 행동
    defensive_actions = player_data[player_data['type_name'].isin(['Tackle', 'Interception', 'Clearance', 'Recovery'])]
    profile['defensive_action_frequency'] = len(defensive_actions) / len(player_data)
    profile['tackle_frequency'] = (player_data['type_name'] == 'Tackle').sum() / len(player_data)
    profile['clearance_frequency'] = (player_data['type_name'] == 'Clearance').sum() / len(player_data)
    
    # 슈팅
    profile['shot_frequency'] = (player_data['type_name'] == 'Shot').sum() / len(player_data)
    
    # 패스 빈도
    profile['pass_frequency'] = len(passes) / len(player_data)
    profile['pass_received_frequency'] = (player_data['type_name'] == 'Pass Received').sum() / len(player_data)
    
    profile['game_count'] = game_count
    profile['event_count'] = event_count
    profile['team_win_rate'] = team_win_rate if team_win_rate is not None else 0.5
    profile['war'] = war if war is not None else 0.0
    profile['war_games_with'] = war_games_with
    profile['war_games_without'] = war_games_without
    
    return profile

def calculate_role_fit_score(player_profile, role_template):
    """롤 적합도 점수 계산 (간단 버전)"""
    from scipy.spatial.distance import cosine, euclidean
    
    if player_profile is None or role_template is None:
        return None
    
    metrics = [
        'forward_pass_ratio', 'long_pass_ratio', 'very_long_pass_ratio', 'short_pass_ratio',
        'average_pass_length', 'pass_success_rate', 'forward_pass_success_rate',
        'average_forward_pass_distance', 'average_carry_length', 'carry_frequency',
        'average_touch_x', 'average_touch_y', 'touch_zone_central', 'touch_zone_wide',
        'touch_zone_defensive', 'touch_zone_midfield', 'touch_zone_forward',
        'defensive_action_frequency', 'tackle_frequency', 'clearance_frequency',
        'shot_frequency', 'pass_frequency', 'pass_received_frequency'
    ]
    
    player_vector = np.array([player_profile.get(m, 0) for m in metrics])
    role_vector = np.array([role_template.get(m, 0) for m in metrics])
    
    # 코사인 유사도
    player_norm = player_vector / (np.linalg.norm(player_vector) + 1e-10)
    role_norm = role_vector / (np.linalg.norm(role_vector) + 1e-10)
    cosine_sim = 1 - cosine(player_norm, role_norm)
    
    # 유클리드 거리
    max_values = np.maximum(np.abs(player_vector), np.abs(role_vector))
    max_values = np.maximum(max_values, 1.0)
    player_normalized = player_vector / max_values
    role_normalized = role_vector / max_values
    euclidean_dist = euclidean(player_normalized, role_normalized)
    max_possible_dist = np.sqrt(len(metrics))
    euclidean_score = 1 - (euclidean_dist / max_possible_dist)
    euclidean_score = max(0, min(1, euclidean_score))
    
    # 가중 평균
    combined_score = 0.6 * cosine_sim + 0.4 * euclidean_score
    raw_score = combined_score * 100
    
    # 표본 크기 보정
    game_count = player_profile.get('game_count', 0)
    event_count = player_profile.get('event_count', 0)
    min_games = 5
    min_events = 200
    
    game_confidence = min(1.0, game_count / min_games) if game_count > 0 else 0
    event_confidence = min(1.0, event_count / min_events) if event_count > 0 else 0
    confidence = np.sqrt(game_confidence * event_confidence)
    
    prior_score = 50.0
    adjusted_score = confidence * raw_score + (1 - confidence) * prior_score
    
    # 경기 수 보너스
    game_bonus = 0.0
    if game_count >= 30:
        game_bonus = 3.0
    elif game_count >= 25:
        game_bonus = 2.0
    elif game_count >= 20:
        game_bonus = 1.0
    elif game_count >= 15:
        game_bonus = 0.5
    
    # WAR 기반 보너스 (Wins Above Replacement)
    # WAR는 선수가 뛴 경기 승률 - 선수가 뛰지 않은 경기 승률
    # 약팀에서도 승리에 기여한 선수를 평가할 수 있음
    war = player_profile.get('war', 0.0)
    war_bonus = 0.0
    
    # WAR가 높을수록 보너스 (최대 +3.0점)
    if war >= 0.3:  # 30%p 이상 개선
        war_bonus = 3.0
    elif war >= 0.2:  # 20%p 이상 개선
        war_bonus = 2.0
    elif war >= 0.1:  # 10%p 이상 개선
        war_bonus = 1.0
    elif war >= 0.05:  # 5%p 이상 개선
        war_bonus = 0.5
    elif war <= -0.3:  # 30%p 이상 악화
        war_bonus = -3.0
    elif war <= -0.2:  # 20%p 이상 악화
        war_bonus = -2.0
    elif war <= -0.1:  # 10%p 이상 악화
        war_bonus = -1.0
    elif war <= -0.05:  # 5%p 이상 악화
        war_bonus = -0.5
    
    # 기존 팀 승률도 보조 지표로 유지 (하지만 가중치 낮춤)
    team_win_rate = player_profile.get('team_win_rate', 0.5)
    win_rate_bonus = 0.0
    if team_win_rate >= 0.6:
        win_rate_bonus = 0.5  # 기존 1.0에서 0.5로 감소
    elif team_win_rate >= 0.5:
        win_rate_bonus = 0.25  # 기존 0.5에서 0.25로 감소
    elif team_win_rate < 0.3:
        win_rate_bonus = -0.5  # 기존 -1.0에서 -0.5로 완화
    elif team_win_rate < 0.4:
        win_rate_bonus = -0.25  # 기존 -0.5에서 -0.25로 완화
    
    final_score = adjusted_score + game_bonus + war_bonus + win_rate_bonus
    
    return {
        'fit_score': final_score,
        'raw_score': raw_score,
        'confidence': confidence,
        'cosine_score': cosine_sim * 100,
        'euclidean_score': euclidean_score * 100,
        'game_bonus': game_bonus,
        'war_bonus': war_bonus,
        'win_rate_bonus': win_rate_bonus
    }

def find_best_role_for_player(player_profile, role_templates, position):
    """선수에게 가장 적합한 롤 찾기"""
    if player_profile is None or position not in role_templates:
        return None, 0, {}
    
    best_role = None
    best_score = 0
    best_details = {}
    
    for role_name, role_info in role_templates[position].items():
        template = role_info.get('template', {})
        result = calculate_role_fit_score(player_profile, template)
        
        if result and result['fit_score'] > best_score:
            best_score = result['fit_score']
            best_role = role_name
            best_details = result
    
    return best_role, best_score, best_details

def generate_all_teams_data():
    """모든 팀의 선수 데이터 생성"""
    print("="*80)
    print("모든 팀의 선수 분석 데이터 생성")
    print("="*80)
    
    df, match_info_df = load_data()
    role_templates = load_role_templates()
    
    # 모든 팀 목록
    all_teams = df.groupby(['team_id', 'team_name_ko']).size().reset_index(name='count')
    all_teams = all_teams.sort_values('team_name_ko')
    
    print(f"\n총 {len(all_teams)}개 팀 발견")
    
    teams_data = {}
    
    for idx, team_row in all_teams.iterrows():
        team_id = team_row['team_id']
        team_name = team_row['team_name_ko']
        
        print(f"\n[{idx+1}/{len(all_teams)}] {team_name} 분석 중...")
        
        # 팀의 모든 선수
        team_players = df[df['team_id'] == team_id].groupby(['player_id', 'player_name_ko', 'main_position']).size().reset_index(name='count')
        team_players = team_players[team_players['count'] >= 200]  # 최소 200개 이벤트
        
        players_list = []
        
        for _, player_row in team_players.iterrows():
            player_id = player_row['player_id']
            player_name = player_row['player_name_ko']
            position = player_row['main_position']
            
            if pd.isna(player_id) or pd.isna(position):
                continue
            
            # 선수 프로파일 계산
            profile = calculate_player_profile(df, player_id, match_info_df)
            if profile is None:
                continue
            
            # 가장 적합한 롤 찾기
            best_role, fit_score, score_details = find_best_role_for_player(profile, role_templates, position)
            
            if best_role is None:
                continue
            
            players_list.append({
                'player_id': float(player_id),
                'player_name': player_name,
                'position': position,
                'role': best_role,
                'fit_score': round(fit_score, 1),
                'score_details': {
                    'raw_score': round(score_details.get('raw_score', 0), 1),
                    'confidence': round(score_details.get('confidence', 0), 3),
                    'cosine_score': round(score_details.get('cosine_score', 0), 1),
                    'euclidean_score': round(score_details.get('euclidean_score', 0), 1),
                    'game_bonus': round(score_details.get('game_bonus', 0), 1),
                    'win_rate_bonus': round(score_details.get('win_rate_bonus', 0), 1),
                },
                'game_count': int(profile.get('game_count', 0)),
                'event_count': int(profile.get('event_count', 0)),
                'team_win_rate': round(profile.get('team_win_rate', 0.5), 3),
                'war': round(profile.get('war', 0.0), 3),
                'war_games_with': int(profile.get('war_games_with', 0)),
                'war_games_without': int(profile.get('war_games_without', 0)),
            })
        
        if len(players_list) > 0:
            teams_data[team_name] = {
                'team_id': int(team_id),
                'team_name': team_name,
                'players': players_list
            }
            print(f"  → {len(players_list)}명의 선수 분석 완료")
    
    # JSON 파일로 저장
    output_path = PROJECT_ROOT / 'docs' / 'data' / 'teams_data.json'
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(teams_data, f, ensure_ascii=False, indent=2)
    
    print(f"\n✓ 데이터 저장 완료: {output_path}")
    print(f"  총 {len(teams_data)}개 팀, {sum(len(t['players']) for t in teams_data.values())}명의 선수")
    
    return teams_data

if __name__ == '__main__':
    generate_all_teams_data()


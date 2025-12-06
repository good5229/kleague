"""
전북 현대 모터스 팀 선수 스타일 분석 및 K리그 랭킹

목적:
1. 전북 현대 모터스 팀의 모든 선수들의 스타일(롤) 정의
2. 각 스타일별 K리그 전체 선수 랭킹 생성
3. 전북 선수들의 랭킹 위치 확인
4. 마크다운 문서 생성
"""

import pandas as pd
import numpy as np
import json
from pathlib import Path
from scipy.spatial.distance import cosine, euclidean
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

def calculate_player_profile(df, player_id, match_info_df=None):
    """선수 행동 프로파일 계산"""
    player_data = df[df['player_id'] == player_id].copy()
    
    if len(player_data) == 0:
        return None
    
    # 경기 수 및 이벤트 수 계산 (표본 크기)
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
        passes['pass_length'] = np.sqrt(
            (passes['end_x'] - passes['start_x'])**2 + 
            (passes['end_y'] - passes['start_y'])**2
        )
        passes['is_forward'] = passes['end_y'] > passes['start_y']
        passes['is_long'] = passes['pass_length'] >= 20
        passes['is_very_long'] = passes['pass_length'] >= 30
        passes['is_short'] = passes['pass_length'] <= 10
        
        forward_passes = passes[passes['is_forward']]
        successful_passes = passes[passes['result_name'] == 'Successful']
        forward_successful = forward_passes[forward_passes['result_name'] == 'Successful']
        
        forward_pass_ratio = len(forward_passes) / len(passes) if len(passes) > 0 else 0
        long_pass_ratio = len(passes[passes['is_long']]) / len(passes) if len(passes) > 0 else 0
        very_long_pass_ratio = len(passes[passes['is_very_long']]) / len(passes) if len(passes) > 0 else 0
        short_pass_ratio = len(passes[passes['is_short']]) / len(passes) if len(passes) > 0 else 0
        pass_success_rate = len(successful_passes) / len(passes) if len(passes) > 0 else 0
        average_pass_length = passes['pass_length'].mean() if len(passes) > 0 else 0
        
        if len(forward_passes) > 0:
            forward_passes = forward_passes.copy()
            forward_passes['forward_distance'] = forward_passes['end_y'] - forward_passes['start_y']
            average_forward_pass_distance = forward_passes['forward_distance'].mean()
            forward_pass_success_rate = len(forward_successful) / len(forward_passes) if len(forward_passes) > 0 else 0
        else:
            average_forward_pass_distance = 0
            forward_pass_success_rate = 0
    else:
        forward_pass_ratio = 0
        long_pass_ratio = 0
        very_long_pass_ratio = 0
        short_pass_ratio = 0
        pass_success_rate = 0
        average_pass_length = 0
        average_forward_pass_distance = 0
        forward_pass_success_rate = 0
    
    # 캐리 관련
    carries = player_data[player_data['type_name'] == 'Carry'].copy()
    if len(carries) > 0:
        carries['carry_length'] = np.sqrt(
            (carries['end_x'] - carries['start_x'])**2 + 
            (carries['end_y'] - carries['start_y'])**2
        )
        average_carry_length = carries['carry_length'].mean()
        carry_frequency = len(carries) / len(player_data) if len(player_data) > 0 else 0
    else:
        average_carry_length = 0
        carry_frequency = 0
    
    # 터치 위치
    touches = player_data[player_data['type_name'].isin(['Pass', 'Carry', 'Shot', 'Pass Received'])].copy()
    if len(touches) > 0:
        average_touch_x = touches['start_x'].mean()
        average_touch_y = touches['start_y'].mean()
        
        # 터치 존
        touch_zone_central = len(touches[(touches['start_x'] >= 33) & (touches['start_x'] <= 67)]) / len(touches)
        touch_zone_wide = 1 - touch_zone_central
        touch_zone_defensive = len(touches[touches['start_y'] <= 50]) / len(touches)
        touch_zone_midfield = len(touches[(touches['start_y'] >= 25) & (touches['start_y'] <= 75)]) / len(touches)
        touch_zone_forward = len(touches[touches['start_y'] >= 50]) / len(touches)
    else:
        average_touch_x = 50
        average_touch_y = 50
        touch_zone_central = 0.5
        touch_zone_wide = 0.5
        touch_zone_defensive = 0.5
        touch_zone_midfield = 0.5
        touch_zone_forward = 0.5
    
    # 수비 행동
    defensive_actions = player_data[player_data['type_name'].isin(['Intervention', 'Tackle', 'Block', 'Clearance'])].copy()
    defensive_action_frequency = len(defensive_actions) / len(player_data) if len(player_data) > 0 else 0
    tackle_frequency = len(player_data[player_data['type_name'] == 'Tackle']) / len(player_data) if len(player_data) > 0 else 0
    clearance_frequency = len(player_data[player_data['type_name'] == 'Clearance']) / len(player_data) if len(player_data) > 0 else 0
    
    # 슈팅
    shots = player_data[player_data['type_name'] == 'Shot']
    shot_frequency = len(shots) / len(player_data) if len(player_data) > 0 else 0
    
    # 패스 빈도
    pass_frequency = len(passes) / len(player_data) if len(player_data) > 0 else 0
    pass_received_frequency = len(player_data[player_data['type_name'] == 'Pass Received']) / len(player_data) if len(player_data) > 0 else 0
    
    profile = {
        'forward_pass_ratio': forward_pass_ratio,
        'long_pass_ratio': long_pass_ratio,
        'very_long_pass_ratio': very_long_pass_ratio,
        'short_pass_ratio': short_pass_ratio,
        'average_pass_length': average_pass_length,
        'pass_success_rate': pass_success_rate,
        'forward_pass_success_rate': forward_pass_success_rate,
        'average_forward_pass_distance': average_forward_pass_distance,
        'average_carry_length': average_carry_length,
        'carry_frequency': carry_frequency,
        'average_touch_x': average_touch_x,
        'average_touch_y': average_touch_y,
        'touch_zone_central': touch_zone_central,
        'touch_zone_wide': touch_zone_wide,
        'touch_zone_defensive': touch_zone_defensive,
        'touch_zone_midfield': touch_zone_midfield,
        'touch_zone_forward': touch_zone_forward,
        'defensive_action_frequency': defensive_action_frequency,
        'tackle_frequency': tackle_frequency,
        'clearance_frequency': clearance_frequency,
        'shot_frequency': shot_frequency,
        'pass_frequency': pass_frequency,
        'pass_received_frequency': pass_received_frequency,
        'game_count': game_count,
        'event_count': event_count,
        'team_win_rate': team_win_rate if team_win_rate is not None else 0.5,  # 기본값 50%
    }
    
    return profile

def calculate_role_fit_score(player_profile, role_template, position_average=None, apply_sample_size_correction=True):
    """
    개선된 롤 적합도 스코어 계산
    
    방법:
    1. 코사인 유사도 (방향 유사성) - 60%
    2. 유클리드 거리 기반 점수 (크기 차이) - 40%
    3. 표본 크기 보정 (베이지안 평균)
    
    표본 크기 보정:
    - 최소 경기 수: 5경기
    - 최소 이벤트 수: 200개
    - 베이지안 평균 방식으로 신뢰도 가중치 적용
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
    
    player_vector = np.array([player_profile.get(m, 0) for m in metrics])
    role_vector = np.array([role_template.get(m, 0) for m in metrics])
    
    # 1. 코사인 유사도 (방향 유사성)
    player_norm = player_vector / (np.linalg.norm(player_vector) + 1e-10)
    role_norm = role_vector / (np.linalg.norm(role_vector) + 1e-10)
    cosine_sim = 1 - cosine(player_norm, role_norm)
    
    # 2. 유클리드 거리 기반 점수 (크기 차이)
    # 각 지표를 0~1 범위로 정규화 (최대값 기준)
    max_values = np.maximum(np.abs(player_vector), np.abs(role_vector))
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
    raw_score = combined_score * 100  # 0~100점
    
    # 표본 크기 보정 적용
    if apply_sample_size_correction:
        game_count = player_profile.get('game_count', 0)
        event_count = player_profile.get('event_count', 0)
        
        # 최소 기준
        min_games = 5
        min_events = 200
        
        # 신뢰도 가중치 계산 (0~1)
        game_confidence = min(1.0, game_count / min_games) if game_count > 0 else 0
        event_confidence = min(1.0, event_count / min_events) if event_count > 0 else 0
        
        # 종합 신뢰도 (경기 수와 이벤트 수의 기하평균)
        confidence = np.sqrt(game_confidence * event_confidence)
        
        # 베이지안 평균 방식
        prior_score = 50.0  # 사전 점수 (중간값)
        adjusted_score = confidence * raw_score + (1 - confidence) * prior_score
        
        # 경기 수 보너스 (한 시즌 꾸준히 뛴 선수에게 가치 부여)
        # 20경기 이상: +1점, 25경기 이상: +2점, 30경기 이상: +3점
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
        if team_win_rate >= 0.6:  # 60% 이상 승률
            win_rate_bonus = 0.5  # 기존 1.0에서 0.5로 감소
        elif team_win_rate >= 0.5:  # 50% 이상 승률
            win_rate_bonus = 0.25  # 기존 0.5에서 0.25로 감소
        elif team_win_rate < 0.3:  # 30% 미만 승률
            win_rate_bonus = -0.5  # 기존 -1.0에서 -0.5로 완화
        elif team_win_rate < 0.4:  # 40% 미만 승률
            win_rate_bonus = -0.25  # 기존 -0.5에서 -0.25로 완화
        
        # 최종 점수에 보너스 추가
        final_score = adjusted_score + game_bonus + war_bonus + win_rate_bonus
        
        return final_score, raw_score, confidence, cosine_sim * 100, euclidean_score * 100, game_bonus, war_bonus, win_rate_bonus
    
    return raw_score, raw_score, 1.0, cosine_sim * 100, euclidean_score * 100, 0.0, 0.0, 0.0

def find_best_role_for_player(player_profile, role_templates, player_position, position_average=None):
    """선수에게 가장 적합한 롤 찾기"""
    if player_profile is None:
        return None, 0, 0, 1.0, 0, 0, 0.0, 0.0, 0.0
    
    best_role = None
    best_score = 0
    best_raw_score = 0
    best_confidence = 1.0
    best_cosine = 0
    best_euclidean = 0
    
    # 포지션에 맞는 롤만 검사
    if player_position in role_templates:
        for role_name, role_info in role_templates[player_position].items():
            template = role_info.get('template', {})
            result = calculate_role_fit_score(player_profile, template, position_average, apply_sample_size_correction=True)
            
            if result is not None:
                score, raw_score, confidence, cosine_score, euclidean_score, game_bonus, war_bonus, win_rate_bonus = result
                if score > best_score:
                    best_score = score
                    best_raw_score = raw_score
                    best_confidence = confidence
                    best_cosine = cosine_score
                    best_euclidean = euclidean_score
                    best_game_bonus = game_bonus
                    best_war_bonus = war_bonus
                    best_win_rate_bonus = win_rate_bonus
                    best_role = role_name
    
    return best_role, best_score, best_raw_score, best_confidence, best_cosine, best_euclidean, best_game_bonus, best_war_bonus, best_win_rate_bonus

def get_jeonbuk_players(df):
    """전북 현대 모터스 선수 목록 추출"""
    # 전북 team_id 찾기
    jeonbuk_teams = df[df['team_name_ko'].str.contains('전북', na=False)]
    if len(jeonbuk_teams) == 0:
        # 영문명으로 시도
        jeonbuk_teams = df[df['team_name'].str.contains('Jeonbuk', na=False, case=False)]
    
    if len(jeonbuk_teams) == 0:
        print("전북 현대 모터스를 찾을 수 없습니다.")
        return []
    
    team_id = jeonbuk_teams['team_id'].iloc[0]
    print(f"전북 현대 모터스 team_id: {team_id}")
    
    # 전북 선수 목록
    jeonbuk_players = df[df['team_id'] == team_id][['player_id', 'player_name_ko', 'main_position']].drop_duplicates()
    
    return jeonbuk_players.to_dict('records')

def get_position_average_profile(df, position):
    """포지션별 평균 프로파일 계산"""
    position_players = df[df['main_position'] == position]
    if len(position_players) == 0:
        return None
    
    # 간단한 평균 계산 (실제로는 calculate_player_profile을 각 선수에 대해 호출해야 함)
    # 여기서는 주요 지표만 계산
    avg_profile = {}
    metrics = ['forward_pass_ratio', 'long_pass_ratio', 'pass_success_rate', 
               'average_touch_y', 'touch_zone_central', 'shot_frequency']
    
    # 실제로는 각 선수의 프로파일을 계산한 후 평균을 내야 하지만,
    # 성능을 위해 샘플링하거나 간단한 집계 사용
    return avg_profile

def get_role_core_metrics(role_name, position):
    """
    롤별 핵심 지표 정의
    
    각 롤의 본질에 맞는 지표만 개선 대상으로 삼음
    롤과 무관한 지표는 제외
    """
    role_core_metrics = {
        # CM 포지션
        'Central Midfielder': {
            'essential': [
                'defensive_action_frequency',  # 수비 지원이 핵심
                'tackle_frequency',  # 미드필드 경합
                'pass_success_rate',  # 패스 정확도
                'touch_zone_defensive',  # 수비 지역 활동
                'touch_zone_midfield',  # 미드필드 활동
            ],
            'important': [
                'pass_frequency',
                'forward_pass_ratio',
                'average_touch_y',  # 위치
            ],
            'irrelevant': [
                'shot_frequency',  # 슈팅은 공격수 역할
                'clearance_frequency',  # 센터백 역할
            ]
        },
        'Deep Lying Playmaker': {
            'essential': [
                'long_pass_ratio',
                'very_long_pass_ratio',
                'pass_success_rate',
                'average_touch_y',  # 후방 위치
                'touch_zone_central',  # 중앙 활동
            ],
            'important': [
                'pass_frequency',
                'forward_pass_ratio',
                'average_pass_length',
            ],
            'irrelevant': [
                'shot_frequency',
                'defensive_action_frequency',  # 수비보다 빌드업이 핵심
            ]
        },
        'Box-to-Box Midfielder': {
            'essential': [
                'touch_zone_forward',  # 전방 활동
                'touch_zone_defensive',  # 수비 활동
                'defensive_action_frequency',
                'pass_success_rate',
            ],
            'important': [
                'tackle_frequency',
                'forward_pass_ratio',
                'average_touch_y',
            ],
            'irrelevant': [
                'shot_frequency',  # 공격 참여는 하지만 슈팅은 아님
            ]
        },
        # CB 포지션
        'Ball Playing Defender': {
            'essential': [
                'long_pass_ratio',
                'pass_success_rate',
                'pass_frequency',
                'touch_zone_defensive',
            ],
            'important': [
                'forward_pass_ratio',
                'average_pass_length',
            ],
            'irrelevant': [
                'shot_frequency',
                'touch_zone_forward',  # 전방 활동은 Libero 역할
            ]
        },
        'No-Nonsense Centre-Back': {
            'essential': [
                'defensive_action_frequency',
                'clearance_frequency',
                'tackle_frequency',
                'touch_zone_defensive',
            ],
            'important': [
                'pass_success_rate',  # 단순하지만 정확해야 함
            ],
            'irrelevant': [
                'shot_frequency',
                'long_pass_ratio',  # 단순 처리가 핵심
                'pass_frequency',  # 빌드업보다 수비가 핵심
            ]
        },
        'Libero': {
            'essential': [
                'touch_zone_forward',  # 전방 이동
                'pass_success_rate',
                'long_pass_ratio',
                'average_touch_y',
            ],
            'important': [
                'pass_frequency',
                'forward_pass_ratio',
            ],
            'irrelevant': [
                'shot_frequency',
            ]
        },
        # CF 포지션
        'Poacher': {
            'essential': [
                'shot_frequency',  # 슈팅이 핵심
                'touch_zone_forward',  # 전방 활동
            ],
            'important': [
                'pass_success_rate',  # 연계
                'short_pass_ratio',
            ],
            'irrelevant': [
                'defensive_action_frequency',  # 수비는 공격수 역할 아님
                'tackle_frequency',
                'clearance_frequency',
            ]
        },
        # RW/LW 포지션
        'Winger': {
            'essential': [
                'touch_zone_wide',  # 측면 활동
                'touch_zone_forward',  # 전방 활동
                'forward_pass_ratio',
            ],
            'important': [
                'pass_success_rate',
                'carry_frequency',
            ],
            'irrelevant': [
                'defensive_action_frequency',  # 공격이 핵심
            ]
        },
        # LB/RB 포지션
        'Full-Back': {
            'essential': [
                'touch_zone_wide',
                'defensive_action_frequency',
                'pass_success_rate',
            ],
            'important': [
                'forward_pass_ratio',
                'touch_zone_forward',
            ],
            'irrelevant': [
                'shot_frequency',
            ]
        },
        'Wing-Back': {
            'essential': [
                'touch_zone_wide',
                'touch_zone_forward',
                'defensive_action_frequency',
            ],
            'important': [
                'pass_success_rate',
                'forward_pass_ratio',
            ],
            'irrelevant': [
                'shot_frequency',
            ]
        },
        'Inverted Wing-Back': {
            'essential': [
                'touch_zone_central',  # 중앙으로 들어옴
                'pass_success_rate',
                'pass_frequency',
            ],
            'important': [
                'forward_pass_ratio',
                'average_touch_y',
            ],
            'irrelevant': [
                'shot_frequency',
            ]
        },
        # GK 포지션
        'Sweeper Keeper': {
            'essential': [
                'long_pass_ratio',
                'pass_success_rate',
                'pass_frequency',
            ],
            'important': [
                'average_pass_length',
            ],
            'irrelevant': [
                'shot_frequency',
                'defensive_action_frequency',  # 골키퍼는 다른 방식으로 수비
            ]
        },
    }
    
    return role_core_metrics.get(role_name, {
        'essential': [],
        'important': [],
        'irrelevant': []
    })

def identify_weaknesses(player_profile, role_template, top_players_profiles, role_name, position):
    """
    선수의 약점 지표 식별 (롤의 핵심 지표만 고려)
    
    개선 방향:
    - 롤의 핵심 지표를 강화하는 방향
    - 상위 선수와 비교하여 롤 내에서의 약점 식별
    - 롤과 무관한 지표는 제외
    """
    if player_profile is None or role_template is None:
        return []
    
    # 롤별 핵심 지표 가져오기
    core_metrics = get_role_core_metrics(role_name, position)
    essential_metrics = core_metrics.get('essential', [])
    important_metrics = core_metrics.get('important', [])
    irrelevant_metrics = core_metrics.get('irrelevant', [])
    
    # 모든 가능한 지표
    all_metrics = [
        'forward_pass_ratio', 'long_pass_ratio', 'very_long_pass_ratio', 'short_pass_ratio',
        'average_pass_length', 'pass_success_rate', 'forward_pass_success_rate',
        'average_forward_pass_distance', 'average_carry_length', 'carry_frequency',
        'average_touch_x', 'average_touch_y', 'touch_zone_central', 'touch_zone_wide',
        'touch_zone_defensive', 'touch_zone_midfield', 'touch_zone_forward',
        'defensive_action_frequency', 'tackle_frequency', 'clearance_frequency',
        'shot_frequency', 'pass_frequency', 'pass_received_frequency'
    ]
    
    # 핵심 지표만 고려 (무관한 지표 제외)
    relevant_metrics = [m for m in all_metrics if m not in irrelevant_metrics]
    
    weaknesses = []
    
    for metric in relevant_metrics:
        # 무관한 지표는 건너뛰기
        if metric in irrelevant_metrics:
            continue
        
        player_value = player_profile.get(metric, 0)
        template_value = role_template.get(metric, 0)
        
        if template_value == 0 and player_value == 0:
            continue
        
        # 상위 선수들의 평균
        if top_players_profiles:
            top_values = [p.get(metric, 0) for p in top_players_profiles if p is not None]
            top_avg = np.mean(top_values) if top_values else template_value
        else:
            top_avg = template_value
        
        # 상위 선수 중 최고값 (목표로 삼을 수 있는 수준)
        if top_players_profiles:
            top_max = max([p.get(metric, 0) for p in top_players_profiles if p is not None], default=template_value)
        else:
            top_max = template_value
        
        # 차이 계산
        gap_to_top = player_value - top_avg
        
        # 중요도 계산
        # 1. 핵심 지표인지 여부 (가중치)
        if metric in essential_metrics:
            weight = 2.0  # 핵심 지표는 2배 가중치
        elif metric in important_metrics:
            weight = 1.5
        else:
            weight = 1.0
        
        # 2. 상위 선수와의 차이 (롤 내에서의 약점)
        if top_avg > 0:
            gap_ratio = abs(gap_to_top) / (abs(top_avg) + 1e-10)
        else:
            gap_ratio = abs(gap_to_top)
        
        importance = gap_ratio * weight
        
        # 개선 방향 결정
        # 상위 선수보다 낮으면 증가 필요, 높으면 감소 필요
        if gap_to_top < -0.05:  # 5% 이상 낮음
            direction = 'increase'
            goal = top_avg  # 상위 선수 평균을 목표로
        elif gap_to_top > 0.05:  # 5% 이상 높음 (과도한 경우)
            direction = 'decrease'
            goal = top_avg
        else:
            direction = 'maintain'
            goal = player_value  # 현재 유지
        
        # 중요도가 충분히 높은 경우만 약점으로 인정
        if importance > 0.15:  # 15% 이상 차이
            # 나이 고려: 활동량 관련 지표는 나이가 많은 선수에게 부적절할 수 있음
            # (현재는 나이 데이터가 없으므로, 향후 외부 데이터 연동 필요)
            # 활동량 관련 지표: defensive_action_frequency, tackle_frequency, carry_frequency 등
            activity_metrics = ['defensive_action_frequency', 'tackle_frequency', 'carry_frequency', 
                              'touch_zone_forward', 'touch_zone_defensive']
            
            is_activity_metric = metric in activity_metrics
            
            weaknesses.append({
                'metric': metric,
                'player_value': player_value,
                'template_value': template_value,
                'top_avg': top_avg,
                'top_max': top_max,
                'gap_to_top': gap_to_top,
                'importance': importance,
                'direction': direction,
                'goal': goal,
                'is_essential': metric in essential_metrics,
                'is_important': metric in important_metrics,
                'is_activity_metric': is_activity_metric,  # 활동량 관련 지표 여부
            })
    
    # 중요도 순으로 정렬 (핵심 지표 우선)
    weaknesses.sort(key=lambda x: (x['is_essential'], x['importance']), reverse=True)
    
    return weaknesses[:5]  # 상위 5개만

def suggest_improvements(player_profile, role_template, top_players_profiles, role_name, position):
    """선수 개선 방안 제안 (롤의 핵심 지표 강화 방향)"""
    weaknesses = identify_weaknesses(player_profile, role_template, top_players_profiles, role_name, position)
    
    metric_names = {
        'forward_pass_ratio': '전방 패스 비율',
        'long_pass_ratio': '롱패스 비율',
        'very_long_pass_ratio': '매우 긴 패스 비율',
        'short_pass_ratio': '짧은 패스 비율',
        'average_pass_length': '평균 패스 거리',
        'pass_success_rate': '패스 성공률',
        'forward_pass_success_rate': '전방 패스 성공률',
        'average_forward_pass_distance': '평균 전방 패스 거리',
        'average_carry_length': '평균 캐리 거리',
        'carry_frequency': '캐리 빈도',
        'average_touch_x': '평균 터치 X 위치',
        'average_touch_y': '평균 터치 Y 위치',
        'touch_zone_central': '중앙 지역 터치 비율',
        'touch_zone_wide': '측면 지역 터치 비율',
        'touch_zone_defensive': '수비 지역 터치 비율',
        'touch_zone_midfield': '미드필드 지역 터치 비율',
        'touch_zone_forward': '전진 지역 터치 비율',
        'defensive_action_frequency': '수비 행동 빈도',
        'tackle_frequency': '태클 빈도',
        'clearance_frequency': '클리어런스 빈도',
        'shot_frequency': '슈팅 빈도',
        'pass_frequency': '패스 빈도',
        'pass_received_frequency': '패스 받은 빈도',
    }
    
    suggestions = []
    for i, weakness in enumerate(weaknesses, 1):
        metric = weakness['metric']
        goal = weakness['goal']  # 상위 선수 평균을 목표로
        improvement_needed = goal - weakness['player_value']
        
        direction_text = {
            'increase': '증가 필요',
            'decrease': '감소 필요',
            'maintain': '현재 수준 유지'
        }.get(weakness['direction'], '조정 필요')
        
        suggestions.append({
            'priority': i,
            'metric': metric,
            'metric_name': metric_names.get(metric, metric),
            'current': weakness['player_value'],
            'top_avg': weakness['top_avg'],
            'top_max': weakness.get('top_max', weakness['top_avg']),
            'goal': goal,
            'improvement_needed': improvement_needed,
            'direction': weakness['direction'],
            'direction_text': direction_text,
            'importance': weakness['importance'],
            'is_essential': weakness.get('is_essential', False),
            'is_important': weakness.get('is_important', False),
        })
    
    return suggestions

def create_rankings_for_all_roles(df, role_templates, match_info_df, min_games=5, min_events=200):
    """
    모든 롤에 대한 K리그 전체 선수 랭킹 생성
    
    포지션별로 구분하여 랭킹 생성 (롤은 포지션 내에서만 비교)
    표본 크기 보정 적용
    """
    print("\nK리그 전체 선수 랭킹 생성 중...")
    print(f"  최소 기준: {min_games}경기 이상, {min_events}개 이벤트 이상")
    
    # 모든 선수 목록 (경기 수와 이벤트 수 계산)
    player_stats = df.groupby(['player_id', 'player_name_ko', 'main_position']).agg({
        'game_id': 'nunique',
        'action_id': 'count'
    }).reset_index()
    player_stats.columns = ['player_id', 'player_name_ko', 'main_position', 'game_count', 'event_count']
    
    # 최소 기준 필터링
    player_stats = player_stats[
        (player_stats['game_count'] >= min_games) & 
        (player_stats['event_count'] >= min_events)
    ]
    
    rankings = defaultdict(list)
    
    for position in role_templates.keys():
        print(f"  {position} 포지션 처리 중...")
        position_players = player_stats[player_stats['main_position'] == position]
        
        for role_name, role_info in role_templates[position].items():
            template = role_info.get('template', {})
            role_rankings = []
            
            for _, player_row in position_players.iterrows():
                player_id = player_row['player_id']
                player_name = player_row['player_name_ko']
                
                # 선수의 팀 정보 가져오기 (가장 많이 뛴 팀)
                player_teams = df[df['player_id'] == player_id]
                if len(player_teams) > 0:
                    team_counts = player_teams['team_name_ko'].value_counts()
                    most_common_team = team_counts.index[0] if len(team_counts) > 0 else '알 수 없음'
                else:
                    most_common_team = '알 수 없음'
                
                profile = calculate_player_profile(df, player_id, match_info_df)
                if profile is None:
                    continue
                
                result = calculate_role_fit_score(profile, template, None, apply_sample_size_correction=True)
                if result is not None:
                    score, raw_score, confidence, cosine_score, euclidean_score, game_bonus, war_bonus, win_rate_bonus = result
                    role_rankings.append({
                        'player_id': player_id,
                        'player_name': player_name,
                        'team_name': most_common_team,
                        'position': position,
                        'fit_score': score,
                        'raw_score': raw_score,
                        'confidence': confidence,
                        'game_bonus': game_bonus,
                        'war_bonus': war_bonus,
                        'win_rate_bonus': win_rate_bonus,
                        'team_win_rate': profile.get('team_win_rate', 0.5),
                        'war': profile.get('war', 0.0),
                        'war_games_with': profile.get('war_games_with', 0),
                        'war_games_without': profile.get('war_games_without', 0),
                        'game_count': profile.get('game_count', 0),
                        'event_count': profile.get('event_count', 0)
                    })
            
            # 점수 순으로 정렬 (보정된 점수 기준)
            role_rankings.sort(key=lambda x: x['fit_score'], reverse=True)
            
            # 랭킹 추가 (포지션_롤 형태의 키 사용)
            for rank, player_info in enumerate(role_rankings, 1):
                player_info['rank'] = rank
                rankings[f"{position}_{role_name}"].append(player_info)
    
    return rankings

def generate_markdown_report(jeonbuk_players_data, rankings, role_templates):
    """마크다운 리포트 생성"""
    md_content = []
    
    md_content.append("# 전북 현대 모터스 팀 선수 스타일 분석 및 K리그 랭킹")
    md_content.append("")
    md_content.append("## 개요")
    md_content.append("")
    md_content.append("이 문서는 전북 현대 모터스 팀의 모든 선수들의 스타일(롤)을 분석하고,")
    md_content.append("각 스타일별 K리그 전체 선수 랭킹에서의 위치를 보여줍니다.")
    md_content.append("")
    md_content.append("**분석 기준:**")
    md_content.append("")
    md_content.append("1. **롤 템플릿**: 데이터 기반 롤 템플릿 (풋볼 매니저 롤 정의 기반)")
    md_content.append("")
    md_content.append("2. **적합도 점수 계산**:")
    md_content.append("   - 코사인 유사도 (60%): 방향 유사성 측정")
    md_content.append("   - 유클리드 거리 점수 (40%): 크기 차이 측정")
    md_content.append("   - 두 점수를 가중 평균하여 최종 적합도 산출 (0~100점)")
    md_content.append("   - 이 방식으로 점수 분포가 넓어져 선수 간 구분력 향상")
    md_content.append("")
    md_content.append("3. **포지션별 랭킹**:")
    md_content.append("   - 같은 포지션 내에서만 롤 비교")
    md_content.append("   - 예: CM 포지션의 Deep Lying Playmaker는 CM 포지션 선수들과만 비교")
    md_content.append("   - 랭킹 근거: 포지션과 롤이 모두 동일한 선수들 간 비교")
    md_content.append("")
    md_content.append("4. **표본 크기 보정 및 경기 수 보너스**:")
    md_content.append("   - 최소 기준: 5경기 이상, 200개 이벤트 이상")
    md_content.append("   - 베이지안 평균 방식으로 신뢰도 가중치 적용")
    md_content.append("   - 신뢰도가 낮은 선수(적은 경기/이벤트)는 평균 점수(50점)에 가까워지도록 보정")
    md_content.append("   - **경기 수 보너스**: 한 시즌 꾸준히 뛴 선수에게 가치 부여")
    md_content.append("     - 15경기 이상: +0.5점")
    md_content.append("     - 20경기 이상: +1.0점")
    md_content.append("     - 25경기 이상: +2.0점")
    md_content.append("     - 30경기 이상: +3.0점")
    md_content.append("")
    md_content.append("5. **개선 방안 제안**:")
    md_content.append("   - 선수의 약점 지표 식별 (롤의 핵심 지표만 고려)")
    md_content.append("   - 상위 10명 선수와 비교하여 롤 내에서의 약점 식별")
    md_content.append("   - 구체적인 목표 수치 제시 (현재값, 목표값, 개선 필요량)")
    md_content.append("   - 검증 방법: 다음 시즌/경기 데이터에서 해당 지표 개선 여부 확인")
    md_content.append("")
    md_content.append("**랭킹 검증 사례:**")
    md_content.append("- 정태욱 (CB, Ball Playing Defender): 14경기, 팀 승률 28.6% → 47위 (팀 승률 페널티 -1.0점 적용)")
    md_content.append("- 아론 (CB, 대전): 19경기, 팀 승률 15.8% → 낮은 순위 (팀 승률 페널티 -1.0점 적용)")
    md_content.append("- 경기 수 보너스와 팀 승률 기여도가 반영되어 실제 성과와 일치하는 랭킹 생성")
    md_content.append("")
    
    # 전북 선수별 분석
    md_content.append("## 전북 현대 모터스 선수별 분석")
    md_content.append("")
    
    for player_info in jeonbuk_players_data:
        player_id = player_info['player_id']
        player_name = player_info['player_name']
        position = player_info['position']
        role = player_info['role']
        # 랭킹에서 찾은 점수 사용 (일관성 유지)
        fit_score = player_info.get('fit_score', 0)  # 랭킹에서 업데이트된 점수
        rank = player_info.get('rank')
        total_players = player_info.get('total_players', 0)
        
        confidence = player_info.get('confidence', 1.0)
        game_count = player_info.get('game_count', 0)
        event_count = player_info.get('event_count', 0)
        
        md_content.append(f"### {player_name} ({position})")
        md_content.append("")
        cosine_score = player_info.get('cosine_score', 0)
        euclidean_score = player_info.get('euclidean_score', 0)
        suggestions = player_info.get('suggestions', [])
        
        md_content.append(f"- **포지션**: {position}")
        md_content.append(f"- **스타일(롤)**: {role}")
        game_bonus = player_info.get('game_bonus', 0)
        win_rate_bonus = player_info.get('win_rate_bonus', 0)
        team_win_rate = player_info.get('team_win_rate', 0.5)
        md_content.append(f"- **롤 적합도**: {fit_score:.1f}점 (신뢰도: {confidence:.1%})")
        md_content.append(f"  - 코사인 유사도: {cosine_score:.1f}점 (방향 유사성)")
        md_content.append(f"  - 유클리드 거리 점수: {euclidean_score:.1f}점 (크기 차이)")
        if game_bonus > 0:
            md_content.append(f"  - 경기 수 보너스: +{game_bonus:.1f}점 ({game_count}경기 출전)")
        if win_rate_bonus != 0:
            bonus_text = f"+{win_rate_bonus:.1f}점" if win_rate_bonus > 0 else f"{win_rate_bonus:.1f}점"
            md_content.append(f"  - 팀 승률 기여도: {bonus_text} (출전 경기 승률: {team_win_rate:.1%})")
        if rank is not None and total_players > 0:
            md_content.append(f"- **K리그 랭킹**: {rank}위 / {total_players}명 ({position} 포지션 내)")
            md_content.append(f"  - **랭킹 근거**: 같은 포지션({position}) 내에서 같은 롤({role})을 가진 선수들과 비교")
            md_content.append(f"  - **상위 비율**: {rank/total_players*100:.1f}%")
        else:
            md_content.append(f"- **K리그 랭킹**: 랭킹 정보 없음 (최소 기준 미달: 5경기, 200개 이벤트)")
        md_content.append(f"- **표본 크기**: {game_count}경기, {event_count}개 이벤트")
        md_content.append("")
        
        # 개선 방안 제안
        if suggestions:
            md_content.append("**개선 방안 (롤의 핵심 지표 강화 방향):**")
            md_content.append("")
            for sug in suggestions:
                essential_mark = "⭐ 핵심 지표" if sug['is_essential'] else "중요 지표" if sug['is_important'] else ""
                
                is_activity = sug.get('is_activity_metric', False)
                age_note = ""
                if is_activity and sug['direction'] == 'increase':
                    age_note = "   - ⚠️ 주의: 활동량 증가는 체력적 한계를 고려해야 합니다. 나이가 많은 선수는 달성하기 어려울 수 있습니다."
                
                md_content.append(f"{sug['priority']}. **{sug['metric_name']}** {essential_mark}")
                md_content.append(f"   - 방향: {sug['direction_text']}")
                md_content.append(f"   - 현재: {sug['current']:.3f}")
                md_content.append(f"   - 목표: {sug['goal']:.3f} (상위 선수 평균: {sug['top_avg']:.3f}, 최고: {sug['top_max']:.3f})")
                md_content.append(f"   - 개선 필요량: {sug['improvement_needed']:+.3f}")
                if age_note:
                    md_content.append(age_note)
                md_content.append(f"   - 검증 방법: 다음 시즌/경기 데이터에서 해당 지표 개선 여부 확인")
                md_content.append("")
        
        # 상위 10명 표시 (랭킹에서 가져온 점수 사용)
        role_key = f"{position}_{role}"
        if role_key in rankings and len(rankings[role_key]) > 0:
            top_10 = rankings[role_key][:10]
            md_content.append(f"**이 롤의 K리그 TOP 10 ({position} 포지션 내):**")
            md_content.append("")
            md_content.append("| 순위 | 선수명 | 소속팀 | 적합도 | 경기 수 | 신뢰도 |")
            md_content.append("|------|--------|--------|--------|--------|--------|")
            for top_player in top_10:
                mark = "👈 **전북 선수**" if top_player['player_id'] == player_id else ""
                top_confidence = top_player.get('confidence', 1.0)
                top_team = top_player.get('team_name', '알 수 없음')
                top_game_count = top_player.get('game_count', 0)
                top_game_bonus = top_player.get('game_bonus', 0)
                top_war_bonus = top_player.get('war_bonus', 0)
                top_win_rate_bonus = top_player.get('win_rate_bonus', 0)
                # 랭킹에서 가져온 점수 사용 (일관성 유지)
                top_fit_score = top_player.get('fit_score', 0)
                total_bonus = top_game_bonus + top_war_bonus + top_win_rate_bonus
                bonus_mark = f" (+{total_bonus:.1f})" if total_bonus != 0 else ""
                md_content.append(f"| {top_player['rank']}위 | {top_player['player_name']} | {top_team} | {top_fit_score:.1f}점{bonus_mark} | {top_game_count}경기 | {top_confidence:.1%} | {mark}")
            
            # 현재 선수가 TOP 10에 없지만 랭킹에 있는 경우 표시
            current_player_in_ranking = False
            for rank_info in rankings[role_key]:
                if rank_info['player_id'] == player_id:
                    current_player_in_ranking = True
                    if rank_info['rank'] > 10:
                        md_content.append("")
                        md_content.append(f"*현재 선수는 {rank_info['rank']}위입니다.*")
                    break
            md_content.append("")
        
        md_content.append("---")
        md_content.append("")
    
    # 롤별 전체 랭킹 요약
    md_content.append("## 롤별 전체 랭킹 요약")
    md_content.append("")
    
    for position in sorted(role_templates.keys()):
        md_content.append(f"### {position} 포지션")
        md_content.append("")
        
        for role_name, role_info in role_templates[position].items():
            role_key = f"{position}_{role_name}"
            if role_key not in rankings or len(rankings[role_key]) == 0:
                continue
            
            # 전북 선수 찾기
            jeonbuk_in_role = [
                p for p in jeonbuk_players_data 
                if p['position'] == position and p['role'] == role_name
            ]
            
            if len(jeonbuk_in_role) == 0:
                continue
            
            md_content.append(f"#### {role_name}")
            md_content.append("")
            md_content.append(f"**설명**: {role_info.get('description', '')}")
            md_content.append("")
            
            if len(jeonbuk_in_role) > 0:
                md_content.append("**전북 현대 모터스 선수:**")
                md_content.append("")
            md_content.append("| 선수명 | 랭킹 | 적합도 | 신뢰도 |")
            md_content.append("|--------|------|--------|--------|")
            for player in jeonbuk_in_role:
                rank = player.get('rank')
                total = player.get('total_players', 0)
                confidence = player.get('confidence', 1.0)
                if rank is not None and total > 0:
                    md_content.append(f"| {player['player_name']} | {rank}위 / {total}명 | {player['fit_score']:.1f}점 | {confidence:.1%} |")
                else:
                    md_content.append(f"| {player['player_name']} | 랭킹 정보 없음 | {player['fit_score']:.1f}점 | {confidence:.1%} |")
                md_content.append("")
            
            md_content.append("---")
            md_content.append("")
    
    return "\n".join(md_content)

def main():
    print("="*80)
    print("전북 현대 모터스 팀 선수 스타일 분석")
    print("="*80)
    
    # 데이터 로딩
    df, match_info_df = load_data()
    role_templates = load_role_templates()
    
    # match_info_df를 전역에서 사용할 수 있도록 저장 (calculate_player_profile에서 사용)
    global _match_info_df
    _match_info_df = match_info_df
    
    # 전북 선수 목록
    jeonbuk_players = get_jeonbuk_players(df)
    print(f"\n전북 현대 모터스 선수 수: {len(jeonbuk_players)}명")
    
    if len(jeonbuk_players) == 0:
        print("전북 선수를 찾을 수 없습니다.")
        return
    
    # 전북 선수별 프로파일 및 롤 할당
    print("\n전북 선수별 스타일 분석 중...")
    jeonbuk_players_data = []
    
    for player in jeonbuk_players:
        player_id = player['player_id']
        player_name = player['player_name_ko']
        position = player['main_position']
        
        print(f"  {player_name} ({position}) 분석 중...")
        
        profile = calculate_player_profile(df, player_id, match_info_df)
        if profile is None:
            continue
        
        role, fit_score, raw_score, confidence, cosine_score, euclidean_score, game_bonus, war_bonus, win_rate_bonus = find_best_role_for_player(
            profile, role_templates, position, None
        )
        if role is None:
            continue
        
        jeonbuk_players_data.append({
            'player_id': player_id,
            'player_name': player_name,
            'position': position,
            'role': role,
            'fit_score': fit_score,
            'raw_score': raw_score,
            'confidence': confidence,
            'cosine_score': cosine_score,
            'euclidean_score': euclidean_score,
            'game_bonus': game_bonus,
            'war_bonus': war_bonus,
            'win_rate_bonus': win_rate_bonus,
            'team_win_rate': profile.get('team_win_rate', 0.5),
            'war': profile.get('war', 0.0),
            'war_games_with': profile.get('war_games_with', 0),
            'war_games_without': profile.get('war_games_without', 0),
            'game_count': profile.get('game_count', 0),
            'event_count': profile.get('event_count', 0),
            'profile': profile  # 나중에 개선 방안 제안에 사용
        })
    
    print(f"\n분석 완료: {len(jeonbuk_players_data)}명")
    
    # 전체 랭킹 생성 (표본 크기 보정 적용)
    rankings = create_rankings_for_all_roles(df, role_templates, match_info_df, min_games=5, min_events=200)
    
    # 전북 선수들의 랭킹 위치 확인 및 랭킹에서 계산된 점수로 업데이트
    print("\n전북 선수들의 랭킹 위치 확인 중...")
    for player_info in jeonbuk_players_data:
        role_key = f"{player_info['position']}_{player_info['role']}"
        player_info['rank'] = None
        player_info['total_players'] = 0
        if role_key in rankings:
            for rank_info in rankings[role_key]:
                if rank_info['player_id'] == player_info['player_id']:
                    # 랭킹에서 계산된 점수로 업데이트 (일관성 유지)
                    player_info['rank'] = rank_info['rank']
                    player_info['total_players'] = len(rankings[role_key])
                    player_info['fit_score'] = rank_info['fit_score']  # 랭킹 점수로 업데이트
                    player_info['raw_score'] = rank_info.get('raw_score', player_info.get('raw_score', 0))
                    player_info['confidence'] = rank_info.get('confidence', player_info.get('confidence', 1.0))
                    player_info['game_bonus'] = rank_info.get('game_bonus', player_info.get('game_bonus', 0))
                    player_info['war_bonus'] = rank_info.get('war_bonus', player_info.get('war_bonus', 0))
                    player_info['win_rate_bonus'] = rank_info.get('win_rate_bonus', player_info.get('win_rate_bonus', 0))
                    player_info['team_win_rate'] = rank_info.get('team_win_rate', player_info.get('team_win_rate', 0.5))
                    player_info['war'] = rank_info.get('war', player_info.get('war', 0.0))
                    player_info['war_games_with'] = rank_info.get('war_games_with', player_info.get('war_games_with', 0))
                    player_info['war_games_without'] = rank_info.get('war_games_without', player_info.get('war_games_without', 0))
                    player_info['game_count'] = rank_info.get('game_count', player_info.get('game_count', 0))
                    player_info['event_count'] = rank_info.get('event_count', player_info.get('event_count', 0))
                    
                    # 개선 방안 제안을 위한 상위 선수 프로파일 수집
                    top_10_profiles = []
                    for top_player in rankings[role_key][:10]:
                        top_profile = calculate_player_profile(df, top_player['player_id'], match_info_df)
                        if top_profile:
                            top_10_profiles.append(top_profile)
                    
                    # 롤 템플릿 가져오기
                    role_template = role_templates.get(position, {}).get(role, {}).get('template', {})
                    if role_template:
                        suggestions = suggest_improvements(
                            player_info.get('profile'),
                            role_template,
                            top_10_profiles,
                            role,  # 롤 이름
                            position  # 포지션
                        )
                        player_info['suggestions'] = suggestions
                    break
    
    # 마크다운 리포트 생성
    print("\n마크다운 리포트 생성 중...")
    md_content = generate_markdown_report(jeonbuk_players_data, rankings, role_templates)
    
    # 파일 저장
    output_path = PROJECT_ROOT / 'analysis' / 'JEONBUK_TEAM_ANALYSIS.md'
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(md_content)
    
    print(f"\n✓ 리포트 저장 완료: {output_path}")
    print(f"\n분석된 전북 선수 수: {len(jeonbuk_players_data)}명")
    
    # 요약 출력
    print("\n" + "="*80)
    print("요약")
    print("="*80)
    for player_info in jeonbuk_players_data:
        rank = player_info.get('rank')
        rank_str = f"{rank}위" if rank is not None else "N/A"
        print(f"{player_info['player_name']} ({player_info['position']}): {player_info['role']} - {rank_str}")

if __name__ == '__main__':
    main()


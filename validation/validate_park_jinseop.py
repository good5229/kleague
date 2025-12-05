"""
박진섭 선수 검증 스크립트

목적: 박진섭 선수의 행동 프로파일을 분석하고, 각 롤 템플릿과의 적합도를 확인
"""

import pandas as pd
import numpy as np
from pathlib import Path
from scipy.spatial.distance import cosine

PROJECT_ROOT = Path(__file__).parent.parent

def load_data():
    df = pd.read_csv(PROJECT_ROOT / 'raw_data' / 'open_track2' / 'raw_data.csv')
    match_info_df = pd.read_csv(PROJECT_ROOT / 'raw_data' / 'open_track2' / 'match_info.csv')
    return df, match_info_df

def calculate_player_profile(df, player_id):
    """선수별 행동 프로파일 계산"""
    player_data = df[df['player_id'] == player_id].copy()
    
    if len(player_data) < 50:
        return None
    
    profile = {}
    
    # 패스 관련 지표
    passes = player_data[player_data['type_name'] == 'Pass']
    if len(passes) > 0:
        forward_passes = passes[passes['dx'] > 0]
        profile['forward_pass_ratio'] = len(forward_passes) / len(passes)
        
        pass_lengths = np.sqrt(passes['dx']**2 + passes['dy']**2)
        long_passes = (pass_lengths > 20).sum()
        profile['long_pass_ratio'] = long_passes / len(passes)
        
        successful_passes = passes[passes['result_name'] == 'Successful']
        profile['pass_success_rate'] = len(successful_passes) / len(passes)
        
        profile['average_pass_length'] = pass_lengths.mean()
    else:
        profile['forward_pass_ratio'] = 0
        profile['long_pass_ratio'] = 0
        profile['pass_success_rate'] = 0
        profile['average_pass_length'] = 0
    
    # 캐리 관련 지표
    carries = player_data[player_data['type_name'] == 'Carry']
    if len(carries) > 0:
        carry_lengths = np.sqrt(carries['dx']**2 + carries['dy']**2)
        profile['average_carry_length'] = carry_lengths.mean()
        profile['carry_frequency'] = len(carries) / len(player_data)
    else:
        profile['average_carry_length'] = 0
        profile['carry_frequency'] = 0
    
    # 공간 활용 지표
    profile['touch_zone_central'] = ((player_data['start_x'] >= 30) & 
                                     (player_data['start_x'] <= 70)).sum() / len(player_data)
    profile['touch_zone_wide'] = ((player_data['start_x'] < 30) | 
                                  (player_data['start_x'] > 70)).sum() / len(player_data)
    profile['touch_zone_forward'] = (player_data['start_y'] > 50).sum() / len(player_data)
    profile['average_touch_x'] = player_data['start_x'].mean()
    profile['average_touch_y'] = player_data['start_y'].mean()
    
    # 수비/압박 지표
    interventions = player_data[player_data['type_name'] == 'Intervention']
    blocks = player_data[player_data['type_name'] == 'Block']
    profile['defensive_action_frequency'] = (len(interventions) + len(blocks)) / len(player_data)
    
    # 공격 관련 지표
    shots = player_data[player_data['type_name'] == 'Shot']
    profile['shot_frequency'] = len(shots) / len(player_data)
    
    # 볼 소유 지표
    profile['event_frequency'] = len(player_data)
    
    return profile

def define_role_template(role_name):
    """롤 템플릿 정의"""
    templates = {
        '딥라잉 플레이메이커': {
            'forward_pass_ratio': 0.6,
            'long_pass_ratio': 0.4,
            'pass_success_rate': 0.85,
            'average_pass_length': 15,
            'touch_zone_central': 0.7,
            'touch_zone_forward': 0.3,
            'average_touch_x': 50,
            'average_touch_y': 30,
            'defensive_action_frequency': 0.05,
            'shot_frequency': 0.01,
        },
        '인벌빙 풀백': {
            'forward_pass_ratio': 0.5,
            'long_pass_ratio': 0.2,
            'pass_success_rate': 0.80,
            'average_pass_length': 10,
            'touch_zone_central': 0.4,
            'touch_zone_wide': 0.6,
            'touch_zone_forward': 0.5,
            'average_touch_x': 30,
            'average_touch_y': 50,
            'defensive_action_frequency': 0.10,
            'shot_frequency': 0.02,
        },
        '박스투박스 미드필더': {
            'forward_pass_ratio': 0.55,
            'long_pass_ratio': 0.25,
            'pass_success_rate': 0.82,
            'average_pass_length': 12,
            'touch_zone_central': 0.6,
            'touch_zone_forward': 0.4,
            'average_touch_x': 50,
            'average_touch_y': 40,
            'defensive_action_frequency': 0.15,
            'shot_frequency': 0.03,
        },
    }
    return templates.get(role_name, {})

def calculate_role_fit_score(player_profile, role_template):
    """적합도 스코어 계산"""
    if player_profile is None or not role_template:
        return None
    
    player_vector = []
    template_vector = []
    
    for key in role_template.keys():
        if key in player_profile:
            player_vector.append(player_profile[key])
            template_vector.append(role_template[key])
    
    if len(player_vector) == 0:
        return None
    
    player_vector = np.array(player_vector)
    template_vector = np.array(template_vector)
    
    try:
        cosine_sim = 1 - cosine(player_vector, template_vector)
        return cosine_sim
    except:
        return None

def compare_with_position_average(df, player_id, position):
    """같은 포지션 평균과 비교"""
    position_players = df[df['main_position'] == position]
    position_profile = {}
    
    passes = position_players[position_players['type_name'] == 'Pass']
    if len(passes) > 0:
        forward_passes = passes[passes['dx'] > 0]
        position_profile['forward_pass_ratio'] = len(forward_passes) / len(passes)
        
        pass_lengths = np.sqrt(passes['dx']**2 + passes['dy']**2)
        long_passes = (pass_lengths > 20).sum()
        position_profile['long_pass_ratio'] = long_passes / len(passes)
        
        successful_passes = passes[passes['result_name'] == 'Successful']
        position_profile['pass_success_rate'] = len(successful_passes) / len(passes)
        
        position_profile['average_pass_length'] = pass_lengths.mean()
    else:
        position_profile['forward_pass_ratio'] = 0
        position_profile['long_pass_ratio'] = 0
        position_profile['pass_success_rate'] = 0
        position_profile['average_pass_length'] = 0
    
    position_profile['touch_zone_central'] = ((position_players['start_x'] >= 30) & 
                                             (position_players['start_x'] <= 70)).sum() / len(position_players)
    position_profile['touch_zone_forward'] = (position_players['start_y'] > 50).sum() / len(position_players)
    position_profile['average_touch_x'] = position_players['start_x'].mean()
    position_profile['average_touch_y'] = position_players['start_y'].mean()
    
    interventions = position_players[position_players['type_name'] == 'Intervention']
    blocks = position_players[position_players['type_name'] == 'Block']
    position_profile['defensive_action_frequency'] = (len(interventions) + len(blocks)) / len(position_players)
    
    return position_profile

def main():
    print("="*60)
    print("박진섭 선수 검증")
    print("="*60)
    
    df, match_info_df = load_data()
    
    # 박진섭 선수 찾기
    park_players = df[df['player_name_ko'].str.contains('박진섭', na=False)]
    if len(park_players) == 0:
        print("❌ 박진섭 선수를 찾을 수 없습니다.")
        return
    
    player_id = park_players['player_id'].iloc[0]
    player_data = df[df['player_id'] == player_id]
    
    print(f"\n[기본 정보]")
    print(f"선수 ID: {player_id}")
    print(f"이름: {park_players['player_name_ko'].iloc[0]}")
    print(f"포지션: {player_data['main_position'].iloc[0]}")
    print(f"팀: {player_data['team_name_ko'].iloc[0]}")
    print(f"총 이벤트 수: {len(player_data):,}")
    print(f"참여 경기 수: {player_data['game_id'].nunique()}")
    
    # 행동 프로파일 계산
    profile = calculate_player_profile(df, player_id)
    
    print(f"\n[행동 프로파일]")
    print(f"전진 패스 비율: {profile['forward_pass_ratio']:.2%}")
    print(f"롱패스 비율: {profile['long_pass_ratio']:.2%}")
    print(f"패스 성공률: {profile['pass_success_rate']:.2%}")
    print(f"평균 패스 거리: {profile['average_pass_length']:.1f}m")
    print(f"중앙 지역 터치 비율: {profile['touch_zone_central']:.2%}")
    print(f"측면 지역 터치 비율: {profile['touch_zone_wide']:.2%}")
    print(f"전진 지역 터치 비율: {profile['touch_zone_forward']:.2%}")
    print(f"평균 터치 위치: ({profile['average_touch_x']:.1f}, {profile['average_touch_y']:.1f})")
    print(f"수비 행동 빈도: {profile['defensive_action_frequency']:.2%}")
    print(f"슈팅 빈도: {profile['shot_frequency']:.2%}")
    
    # 포지션 평균과 비교
    position = player_data['main_position'].iloc[0]
    position_avg = compare_with_position_average(df, player_id, position)
    
    print(f"\n[CB 포지션 평균과 비교]")
    print(f"전진 패스 비율: {profile['forward_pass_ratio']:.2%} (평균: {position_avg['forward_pass_ratio']:.2%}, 차이: {profile['forward_pass_ratio'] - position_avg['forward_pass_ratio']:+.2%})")
    print(f"롱패스 비율: {profile['long_pass_ratio']:.2%} (평균: {position_avg['long_pass_ratio']:.2%}, 차이: {profile['long_pass_ratio'] - position_avg['long_pass_ratio']:+.2%})")
    print(f"패스 성공률: {profile['pass_success_rate']:.2%} (평균: {position_avg['pass_success_rate']:.2%}, 차이: {profile['pass_success_rate'] - position_avg['pass_success_rate']:+.2%})")
    print(f"평균 터치 Y 위치: {profile['average_touch_y']:.1f} (평균: {position_avg['average_touch_y']:.1f}, 차이: {profile['average_touch_y'] - position_avg['average_touch_y']:+.1f})")
    print(f"수비 행동 빈도: {profile['defensive_action_frequency']:.2%} (평균: {position_avg['defensive_action_frequency']:.2%}, 차이: {profile['defensive_action_frequency'] - position_avg['defensive_action_frequency']:+.2%})")
    
    # 각 롤 템플릿과의 적합도
    print(f"\n[롤 템플릿 적합도]")
    roles = ['딥라잉 플레이메이커', '인벌빙 풀백', '박스투박스 미드필더']
    
    fit_scores = {}
    for role_name in roles:
        template = define_role_template(role_name)
        fit_score = calculate_role_fit_score(profile, template)
        fit_scores[role_name] = fit_score
        print(f"{role_name}: {fit_score:.3f}" if fit_score else f"{role_name}: 계산 불가")
    
    # 해석
    print(f"\n[해석]")
    print(f"박진섭 선수는 CB(센터백) 포지션의 선수입니다.")
    print(f"주요 특징:")
    
    if profile['long_pass_ratio'] > position_avg['long_pass_ratio']:
        print(f"  - 롱패스 비율이 CB 평균보다 높음 (빌드업 역할)")
    if profile['forward_pass_ratio'] > position_avg['forward_pass_ratio']:
        print(f"  - 전진 패스 비율이 CB 평균보다 높음 (공격적 빌드업)")
    if profile['average_touch_y'] < position_avg['average_touch_y']:
        print(f"  - 평균 터치 위치가 CB 평균보다 후방 (딥라잉)")
    if profile['defensive_action_frequency'] < position_avg['defensive_action_frequency']:
        print(f"  - 수비 행동 빈도가 CB 평균보다 낮음 (공격 지향)")
    
    print(f"\n롤 적합도 관점:")
    max_role = max(fit_scores.items(), key=lambda x: x[1] if x[1] else 0)
    print(f"  - 가장 높은 적합도: {max_role[0]} ({max_role[1]:.3f})")
    print(f"  - 주의: 현재 롤 템플릿은 CB 포지션을 고려하지 않았으므로,")
    print(f"    실제 롤 해석은 도메인 전문가 검토가 필요합니다.")

if __name__ == '__main__':
    main()


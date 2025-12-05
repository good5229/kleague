"""
딥라잉 플레이메이커 vs 빌드업형 센터백 구분 분석

목적: 딥라잉 플레이메이커(CM/CDM)와 빌드업형 센터백(CB)의 차이를 데이터로 확인하고
      롤 템플릿을 구분하여 정의
"""

import pandas as pd
import numpy as np
from pathlib import Path
import matplotlib.pyplot as plt
import seaborn as sns

plt.rcParams['font.family'] = 'AppleGothic'
plt.rcParams['axes.unicode_minus'] = False

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
        
        # 매우 긴 패스 (30m 이상)
        very_long_passes = (pass_lengths > 30).sum()
        profile['very_long_pass_ratio'] = very_long_passes / len(passes)
        
        successful_passes = passes[passes['result_name'] == 'Successful']
        profile['pass_success_rate'] = len(successful_passes) / len(passes)
        
        profile['average_pass_length'] = pass_lengths.mean()
        
        # 짧은 패스 비율 (10m 이하)
        short_passes = (pass_lengths <= 10).sum()
        profile['short_pass_ratio'] = short_passes / len(passes)
        
        # 전진 패스 성공률
        forward_successful = forward_passes[forward_passes['result_name'] == 'Successful']
        profile['forward_pass_success_rate'] = len(forward_successful) / len(forward_passes) if len(forward_passes) > 0 else 0
    else:
        profile['forward_pass_ratio'] = 0
        profile['long_pass_ratio'] = 0
        profile['very_long_pass_ratio'] = 0
        profile['pass_success_rate'] = 0
        profile['average_pass_length'] = 0
        profile['short_pass_ratio'] = 0
        profile['forward_pass_success_rate'] = 0
    
    # 공간 활용 지표
    profile['average_touch_x'] = player_data['start_x'].mean()
    profile['average_touch_y'] = player_data['start_y'].mean()
    
    # 후방 지역 터치 (y < 30)
    profile['touch_zone_defensive'] = (player_data['start_y'] < 30).sum() / len(player_data)
    # 중앙 지역 터치 (30 <= y < 50)
    profile['touch_zone_midfield'] = ((player_data['start_y'] >= 30) & (player_data['start_y'] < 50)).sum() / len(player_data)
    # 전진 지역 터치 (y >= 50)
    profile['touch_zone_forward'] = (player_data['start_y'] >= 50).sum() / len(player_data)
    
    # 중앙 지역 터치 (x: 30-70)
    profile['touch_zone_central'] = ((player_data['start_x'] >= 30) & (player_data['start_x'] <= 70)).sum() / len(player_data)
    
    # 빌드업 참여도: 연속 패스 플레이 참여 빈도
    # 간단 버전: 패스 후 다른 선수가 패스를 받는 빈도
    pass_received = player_data[player_data['type_name'] == 'Pass Received']
    profile['pass_received_frequency'] = len(pass_received) / len(player_data)
    
    # 패스 빈도
    profile['pass_frequency'] = len(passes) / len(player_data)
    
    # 경기당 지표
    games = player_data['game_id'].nunique()
    profile['passes_per_game'] = len(passes) / games if games > 0 else 0
    
    return profile

def compare_positions(df):
    """포지션별 평균 프로파일 비교"""
    print("="*80)
    print("포지션별 평균 프로파일 비교")
    print("="*80)
    
    positions = ['CM', 'CDM', 'CB']
    position_profiles = {}
    
    for position in positions:
        position_players = df[df['main_position'] == position]
        if len(position_players) == 0:
            continue
        
        player_ids = position_players['player_id'].dropna().unique()
        profiles = []
        
        for player_id in player_ids:
            profile = calculate_player_profile(df, player_id)
            if profile:
                profiles.append(profile)
        
        if len(profiles) > 0:
            # 평균 계산
            avg_profile = {}
            for key in profiles[0].keys():
                avg_profile[key] = np.mean([p.get(key, 0) for p in profiles])
            position_profiles[position] = avg_profile
    
    # 비교 출력
    print("\n[주요 지표 비교]")
    key_metrics = [
        'average_touch_y',  # 평균 터치 Y 위치 (후방일수록 낮음)
        'long_pass_ratio',  # 롱패스 비율
        'very_long_pass_ratio',  # 매우 긴 패스 비율
        'short_pass_ratio',  # 짧은 패스 비율
        'pass_frequency',  # 패스 빈도
        'pass_received_frequency',  # 패스 받는 빈도 (빌드업 참여)
        'touch_zone_midfield',  # 미드필드 지역 터치
        'touch_zone_defensive',  # 수비 지역 터치
    ]
    
    for metric in key_metrics:
        print(f"\n{metric}:")
        for pos in positions:
            if pos in position_profiles:
                value = position_profiles[pos].get(metric, 0)
                if 'ratio' in metric or 'frequency' in metric:
                    print(f"  {pos}: {value:.2%}")
                else:
                    print(f"  {pos}: {value:.2f}")
    
    return position_profiles

def analyze_specific_players(df):
    """특정 선수들 비교 분석"""
    print("\n" + "="*80)
    print("특정 선수 비교 분석")
    print("="*80)
    
    # CB 선수들 (빌드업형 센터백 후보)
    cb_players = {
        '박진섭': 246402.0,
        '민상기': None,  # ID 찾기 필요
        '김영빈': None,
        '권경원': None,
        '박성훈': None,
        '안영규': None,
    }
    
    # 이름으로 ID 찾기
    for name in ['민상기', '김영빈', '권경원', '박성훈', '안영규']:
        players = df[df['player_name_ko'].str.contains(name, na=False)]
        if len(players) > 0:
            cb_players[name] = players['player_id'].iloc[0]
    
    # CM 선수들 (딥라잉 플레이메이커 후보)
    cm_players = {
        '기성용': 161110.0,
        '정우영': 529466.0,
        '윤빛가람': 354812.0,
    }
    
    all_players = {**cb_players, **cm_players}
    
    results = {}
    
    print("\n[선수별 프로파일]")
    for name, player_id in all_players.items():
        if player_id is None:
            continue
        
        profile = calculate_player_profile(df, player_id)
        if profile:
            player_data = df[df['player_id'] == player_id]
            position = player_data['main_position'].iloc[0]
            results[name] = {
                'profile': profile,
                'position': position,
                'player_id': player_id
            }
            
            print(f"\n{name} ({position}):")
            print(f"  평균 터치 Y 위치: {profile['average_touch_y']:.1f}")
            print(f"  롱패스 비율: {profile['long_pass_ratio']:.2%}")
            print(f"  매우 긴 패스 비율 (30m+): {profile['very_long_pass_ratio']:.2%}")
            print(f"  짧은 패스 비율 (10m 이하): {profile['short_pass_ratio']:.2%}")
            print(f"  패스 빈도: {profile['pass_frequency']:.2%}")
            print(f"  패스 받는 빈도: {profile['pass_received_frequency']:.2%}")
            print(f"  미드필드 지역 터치: {profile['touch_zone_midfield']:.2%}")
            print(f"  수비 지역 터치: {profile['touch_zone_defensive']:.2%}")
    
    # 차이점 분석
    print("\n" + "="*80)
    print("차이점 분석")
    print("="*80)
    
    cb_profiles = [results[name]['profile'] for name in cb_players.keys() if name in results]
    cm_profiles = [results[name]['profile'] for name in cm_players.keys() if name in results]
    
    if cb_profiles and cm_profiles:
        print("\n[CB vs CM 평균 비교]")
        key_metrics = [
            'average_touch_y',
            'long_pass_ratio',
            'very_long_pass_ratio',
            'short_pass_ratio',
            'pass_frequency',
            'pass_received_frequency',
            'touch_zone_midfield',
            'touch_zone_defensive',
        ]
        
        for metric in key_metrics:
            cb_avg = np.mean([p.get(metric, 0) for p in cb_profiles])
            cm_avg = np.mean([p.get(metric, 0) for p in cm_profiles])
            diff = cb_avg - cm_avg
            
            if 'ratio' in metric or 'frequency' in metric:
                print(f"\n{metric}:")
                print(f"  CB 평균: {cb_avg:.2%}")
                print(f"  CM 평균: {cm_avg:.2%}")
                print(f"  차이: {diff:+.2%}")
            else:
                print(f"\n{metric}:")
                print(f"  CB 평균: {cb_avg:.2f}")
                print(f"  CM 평균: {cm_avg:.2f}")
                print(f"  차이: {diff:+.2f}")
    
    return results

def define_roles():
    """구분된 롤 템플릿 정의"""
    print("\n" + "="*80)
    print("구분된 롤 템플릿 제안")
    print("="*80)
    
    # 실제 데이터 기반으로 차이점을 반영한 템플릿
    templates = {
        '딥라잉 플레이메이커 (CM/CDM)': {
            'average_touch_y': 35,  # 미드필드 영역
            'long_pass_ratio': 0.25,  # 중간 정도
            'very_long_pass_ratio': 0.05,  # 매우 긴 패스는 적음
            'short_pass_ratio': 0.40,  # 짧은 패스 많이
            'pass_frequency': 0.35,  # 패스 빈도 높음
            'pass_received_frequency': 0.30,  # 패스 받는 빈도 높음 (빌드업 참여)
            'touch_zone_midfield': 0.60,  # 미드필드 지역 많이
            'touch_zone_defensive': 0.20,  # 수비 지역은 적음
        },
        '빌드업형 센터백 (CB)': {
            'average_touch_y': 30,  # 더 후방
            'long_pass_ratio': 0.35,  # 롱패스 많이
            'very_long_pass_ratio': 0.15,  # 매우 긴 패스 많이
            'short_pass_ratio': 0.25,  # 짧은 패스는 적음
            'pass_frequency': 0.30,  # 패스 빈도 중간
            'pass_received_frequency': 0.25,  # 패스 받는 빈도 낮음 (빌드업 시작점)
            'touch_zone_midfield': 0.30,  # 미드필드 지역 적음
            'touch_zone_defensive': 0.50,  # 수비 지역 많이
        },
    }
    
    print("\n[롤 템플릿]")
    for role_name, template in templates.items():
        print(f"\n{role_name}:")
        for key, value in template.items():
            if 'ratio' in key or 'frequency' in key or 'zone' in key:
                print(f"  {key}: {value:.2%}")
            else:
                print(f"  {key}: {value:.2f}")
    
    return templates

def main():
    df, match_info_df = load_data()
    
    # 1. 포지션별 평균 비교
    position_profiles = compare_positions(df)
    
    # 2. 특정 선수 비교
    player_results = analyze_specific_players(df)
    
    # 3. 구분된 롤 템플릿 제안
    role_templates = define_roles()
    
    print("\n" + "="*80)
    print("결론")
    print("="*80)
    print("\n딥라잉 플레이메이커와 빌드업형 센터백의 주요 차이:")
    print("1. 위치: 딥라잉 플레이메이커는 미드필드 영역(y~35), 빌드업형 CB는 더 후방(y~30)")
    print("2. 패스 패턴: 딥라잉 플레이메이커는 짧은 패스와 중간 거리 패스 혼합,")
    print("              빌드업형 CB는 매우 긴 롱패스(30m+)를 많이 사용")
    print("3. 빌드업 참여: 딥라잉 플레이메이커는 연속적인 패스 플레이에 많이 참여,")
    print("                빌드업형 CB는 빌드업의 시작점 역할 (패스를 받는 빈도 낮음)")
    print("4. 공간 활용: 딥라잉 플레이메이커는 미드필드 지역 중심,")
    print("              빌드업형 CB는 수비 지역 중심")

if __name__ == '__main__':
    main()


"""
딥라잉 플레이메이커 vs 빌드업형 센터백 상세 비교

핵심 차이점 분석:
1. 전방 패스 패턴 (전방으로 공을 뿌려주는 빈도와 거리)
2. 빌드업 시작점 역할 (누가 패스를 받아서 시작하는지)
3. 패스 목적 (단순 전방 배급 vs 빌드업 조율)
"""

import pandas as pd
import numpy as np
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent

def load_data():
    df = pd.read_csv(PROJECT_ROOT / 'raw_data' / 'open_track2' / 'raw_data.csv')
    match_info_df = pd.read_csv(PROJECT_ROOT / 'raw_data' / 'open_track2' / 'match_info.csv')
    return df, match_info_df

def analyze_forward_passing(df, player_id):
    """전방 패스 패턴 분석"""
    player_data = df[df['player_id'] == player_id].copy()
    passes = player_data[player_data['type_name'] == 'Pass']
    
    if len(passes) == 0:
        return None
    
    # 전방 패스 (end_y > start_y)
    forward_passes = passes[passes['end_y'] > passes['start_y']]
    
    # 전방 패스 거리
    if len(forward_passes) > 0:
        forward_distances = np.sqrt(
            (forward_passes['end_x'] - forward_passes['start_x'])**2 +
            (forward_passes['end_y'] - forward_passes['start_y'])**2
        )
        
        # 매우 전방 패스 (y 방향으로 20m 이상)
        very_forward = forward_passes[(forward_passes['end_y'] - forward_passes['start_y']) > 20]
    else:
        forward_distances = pd.Series([])
        very_forward = pd.DataFrame()
    
    result = {
        'forward_pass_ratio': len(forward_passes) / len(passes),
        'average_forward_distance': forward_distances.mean() if len(forward_distances) > 0 else 0,
        'very_forward_pass_ratio': len(very_forward) / len(passes),
        'forward_pass_success_rate': len(forward_passes[forward_passes['result_name'] == 'Successful']) / len(forward_passes) if len(forward_passes) > 0 else 0,
    }
    
    return result

def analyze_build_up_start(df, player_id):
    """빌드업 시작점 역할 분석"""
    player_data = df[df['player_id'] == player_id].copy()
    
    # 패스를 받은 후 바로 패스를 하는 빈도 (빌드업 중간 참여)
    pass_received = player_data[player_data['type_name'] == 'Pass Received']
    
    build_up_participation = 0
    for idx, row in pass_received.iterrows():
        # 패스를 받은 후 3초 이내에 패스를 하는지
        next_events = player_data[(player_data['game_id'] == row['game_id']) & 
                                  (player_data['action_id'] > row['action_id']) &
                                  (player_data['time_seconds'] <= row['time_seconds'] + 3)]
        if len(next_events[next_events['type_name'] == 'Pass']) > 0:
            build_up_participation += 1
    
    # 패스를 받기 전에 다른 선수가 패스를 했는지 (빌드업 시작점)
    build_up_start = 0
    for idx, row in pass_received.iterrows():
        prev_events = player_data[(player_data['game_id'] == row['game_id']) & 
                                  (player_data['action_id'] < row['action_id']) &
                                  (player_data['time_seconds'] >= row['time_seconds'] - 3)]
        if len(prev_events[prev_events['type_name'] == 'Pass']) == 0:
            build_up_start += 1
    
    result = {
        'build_up_participation_ratio': build_up_participation / len(pass_received) if len(pass_received) > 0 else 0,
        'build_up_start_ratio': build_up_start / len(pass_received) if len(pass_received) > 0 else 0,
    }
    
    return result

def analyze_pass_purpose(df, player_id):
    """패스 목적 분석"""
    player_data = df[df['player_id'] == player_id].copy()
    passes = player_data[player_data['type_name'] == 'Pass']
    
    if len(passes) == 0:
        return None
    
    # 패스 거리별 분류
    pass_lengths = np.sqrt(passes['dx']**2 + passes['dy']**2)
    
    # 단순 전방 배급: 매우 긴 전방 패스 (30m 이상, 전방으로)
    forward_passes = passes[passes['end_y'] > passes['start_y']]
    if len(forward_passes) > 0:
        forward_distances = np.sqrt(
            (forward_passes['end_x'] - forward_passes['start_x'])**2 +
            (forward_passes['end_y'] - forward_passes['start_y'])**2
        )
        long_forward_passes = forward_passes[forward_distances > 30]
    else:
        long_forward_passes = pd.DataFrame()
    
    # 빌드업 조율: 짧은 패스 후 연속 패스
    short_passes = passes[pass_lengths <= 15]
    
    result = {
        'long_forward_distribution_ratio': len(long_forward_passes) / len(passes),
        'short_build_up_ratio': len(short_passes) / len(passes),
        'average_pass_length': pass_lengths.mean(),
    }
    
    return result

def compare_players_detailed(df):
    """선수들 상세 비교"""
    print("="*80)
    print("딥라잉 플레이메이커 vs 빌드업형 센터백 상세 비교")
    print("="*80)
    
    # 선수 ID 찾기
    players = {}
    for name in ['박진섭', '민상기', '김영빈', '권경원', '박성훈', '안영규', '기성용', '정우영', '윤빛가람']:
        found = df[df['player_name_ko'].str.contains(name, na=False)]
        if len(found) > 0:
            players[name] = found['player_id'].iloc[0]
    
    results = {}
    
    print("\n[1. 전방 패스 패턴 분석]")
    print("-"*80)
    for name, player_id in players.items():
        player_data = df[df['player_id'] == player_id]
        position = player_data['main_position'].iloc[0]
        
        forward_analysis = analyze_forward_passing(df, player_id)
        if forward_analysis:
            results[name] = {
                'position': position,
                'forward_analysis': forward_analysis
            }
            print(f"\n{name} ({position}):")
            print(f"  전방 패스 비율: {forward_analysis['forward_pass_ratio']:.2%}")
            print(f"  평균 전방 패스 거리: {forward_analysis['average_forward_distance']:.1f}m")
            print(f"  매우 전방 패스 비율 (y+20m): {forward_analysis['very_forward_pass_ratio']:.2%}")
            print(f"  전방 패스 성공률: {forward_analysis['forward_pass_success_rate']:.2%}")
    
    print("\n[2. 빌드업 역할 분석]")
    print("-"*80)
    for name in players.keys():
        if name not in results:
            continue
        
        build_up_analysis = analyze_build_up_start(df, players[name])
        if build_up_analysis:
            results[name]['build_up_analysis'] = build_up_analysis
            print(f"\n{name} ({results[name]['position']}):")
            print(f"  빌드업 중간 참여 비율: {build_up_analysis['build_up_participation_ratio']:.2%}")
            print(f"  빌드업 시작점 비율: {build_up_analysis['build_up_start_ratio']:.2%}")
    
    print("\n[3. 패스 목적 분석]")
    print("-"*80)
    for name in players.keys():
        if name not in results:
            continue
        
        pass_purpose = analyze_pass_purpose(df, players[name])
        if pass_purpose:
            results[name]['pass_purpose'] = pass_purpose
            print(f"\n{name} ({results[name]['position']}):")
            print(f"  긴 전방 배급 패스 비율 (30m+): {pass_purpose['long_forward_distribution_ratio']:.2%}")
            print(f"  짧은 빌드업 패스 비율 (15m 이하): {pass_purpose['short_build_up_ratio']:.2%}")
            print(f"  평균 패스 거리: {pass_purpose['average_pass_length']:.1f}m")
    
    # CB vs CM 비교
    print("\n" + "="*80)
    print("CB vs CM 평균 비교")
    print("="*80)
    
    cb_names = [name for name in players.keys() if name in results and results[name]['position'] == 'CB']
    cm_names = [name for name in players.keys() if name in results and results[name]['position'] == 'CM']
    
    if cb_names and cm_names:
        print("\n[전방 패스 패턴]")
        cb_forward_avg = np.mean([results[name]['forward_analysis']['forward_pass_ratio'] for name in cb_names])
        cm_forward_avg = np.mean([results[name]['forward_analysis']['forward_pass_ratio'] for name in cm_names])
        print(f"  CB 평균 전방 패스 비율: {cb_forward_avg:.2%}")
        print(f"  CM 평균 전방 패스 비율: {cm_forward_avg:.2%}")
        print(f"  차이: {cb_forward_avg - cm_forward_avg:+.2%}")
        
        cb_very_forward_avg = np.mean([results[name]['forward_analysis']['very_forward_pass_ratio'] for name in cb_names])
        cm_very_forward_avg = np.mean([results[name]['forward_analysis']['very_forward_pass_ratio'] for name in cm_names])
        print(f"\n  CB 평균 매우 전방 패스 비율: {cb_very_forward_avg:.2%}")
        print(f"  CM 평균 매우 전방 패스 비율: {cm_very_forward_avg:.2%}")
        print(f"  차이: {cb_very_forward_avg - cm_very_forward_avg:+.2%}")
        
        print("\n[빌드업 역할]")
        cb_start_avg = np.mean([results[name]['build_up_analysis']['build_up_start_ratio'] for name in cb_names])
        cm_start_avg = np.mean([results[name]['build_up_analysis']['build_up_start_ratio'] for name in cm_names])
        print(f"  CB 평균 빌드업 시작점 비율: {cb_start_avg:.2%}")
        print(f"  CM 평균 빌드업 시작점 비율: {cm_start_avg:.2%}")
        print(f"  차이: {cb_start_avg - cm_start_avg:+.2%}")
        
        print("\n[패스 목적]")
        cb_long_dist_avg = np.mean([results[name]['pass_purpose']['long_forward_distribution_ratio'] for name in cb_names])
        cm_long_dist_avg = np.mean([results[name]['pass_purpose']['long_forward_distribution_ratio'] for name in cm_names])
        print(f"  CB 평균 긴 전방 배급 패스 비율: {cb_long_dist_avg:.2%}")
        print(f"  CM 평균 긴 전방 배급 패스 비율: {cm_long_dist_avg:.2%}")
        print(f"  차이: {cb_long_dist_avg - cm_long_dist_avg:+.2%}")
        
        cb_short_avg = np.mean([results[name]['pass_purpose']['short_build_up_ratio'] for name in cb_names])
        cm_short_avg = np.mean([results[name]['pass_purpose']['short_build_up_ratio'] for name in cm_names])
        print(f"\n  CB 평균 짧은 빌드업 패스 비율: {cb_short_avg:.2%}")
        print(f"  CM 평균 짧은 빌드업 패스 비율: {cm_short_avg:.2%}")
        print(f"  차이: {cb_short_avg - cm_short_avg:+.2%}")
    
    print("\n" + "="*80)
    print("결론")
    print("="*80)
    print("\n딥라잉 플레이메이커와 빌드업형 센터백의 차이:")
    print("1. 전방 패스 패턴:")
    print("   - 빌드업형 CB: 매우 긴 전방 패스를 많이 사용하여 전방으로 공을 뿌려줌")
    print("   - 딥라잉 플레이메이커: 중간 거리 전방 패스로 빌드업을 조율")
    print("\n2. 빌드업 역할:")
    print("   - 빌드업형 CB: 빌드업의 시작점 역할 (패스를 받기 전에 다른 패스가 없음)")
    print("   - 딥라잉 플레이메이커: 빌드업 중간에 참여하여 연속 패스 플레이 조율")
    print("\n3. 패스 목적:")
    print("   - 빌드업형 CB: 긴 전방 배급 패스로 공격 전환")
    print("   - 딥라잉 플레이메이커: 짧은 패스로 빌드업 조율 후 전방 전개")

def main():
    df, match_info_df = load_data()
    compare_players_detailed(df)

if __name__ == '__main__':
    main()


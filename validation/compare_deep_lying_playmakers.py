"""
딥라잉 플레이메이커 비교 검증 스크립트

목적: 기성용, 정우영, 윤빛가람, 박진섭 선수들을 비교하여
      - 이들이 딥라잉 플레이메이커로 부를 만한지
      - 박진섭이 CB 포지션이지만 딥라잉 플레이메이커처럼 플레이하는지 검증
"""

import pandas as pd
import numpy as np
from pathlib import Path
from scipy.spatial.distance import cosine
import matplotlib.pyplot as plt
import seaborn as sns

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
    
    # 추가 지표: 빌드업 참여도
    profile['pass_frequency'] = len(passes) / len(player_data)
    profile['event_frequency'] = len(player_data)
    
    return profile

def define_deep_lying_playmaker_template():
    """딥라잉 플레이메이커 템플릿"""
    return {
        'forward_pass_ratio': 0.6,  # 높음 (전진 패스 많이)
        'long_pass_ratio': 0.4,     # 높음 (롱패스 자주)
        'pass_success_rate': 0.85,  # 높음 (정확한 패스)
        'average_pass_length': 15,   # 중간-높음
        'touch_zone_central': 0.7,   # 높음 (중앙 지역)
        'touch_zone_forward': 0.3,   # 낮음 (수비 라인 근처)
        'average_touch_x': 50,       # 중앙
        'average_touch_y': 30,       # 후방
        'defensive_action_frequency': 0.05,  # 낮음 (공격 지향)
        'shot_frequency': 0.01,      # 낮음 (슈팅 적음)
        'pass_frequency': 0.3,       # 높음 (패스 많이)
    }

def calculate_role_fit_score(player_profile, role_template):
    """적합도 스코어 계산 (코사인 유사도)"""
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

def compare_players(df, player_ids, player_names):
    """여러 선수 비교"""
    print("="*80)
    print("딥라잉 플레이메이커 비교 분석")
    print("="*80)
    
    template = define_deep_lying_playmaker_template()
    
    results = []
    
    for player_id, player_name in zip(player_ids, player_names):
        player_data = df[df['player_id'] == player_id]
        if len(player_data) == 0:
            continue
        
        profile = calculate_player_profile(df, player_id)
        if profile is None:
            continue
        
        fit_score = calculate_role_fit_score(profile, template)
        
        position = player_data['main_position'].iloc[0]
        team = player_data['team_name_ko'].iloc[0]
        games = player_data['game_id'].nunique()
        events = len(player_data)
        
        results.append({
            'name': player_name,
            'player_id': player_id,
            'position': position,
            'team': team,
            'games': games,
            'events': events,
            'profile': profile,
            'fit_score': fit_score
        })
        
        print(f"\n[{player_name}]")
        print(f"  포지션: {position}")
        print(f"  팀: {team}")
        print(f"  경기 수: {games}, 이벤트 수: {events:,}")
        print(f"  딥라잉 플레이메이커 적합도: {fit_score:.3f}" if fit_score else "  적합도: 계산 불가")
        print(f"\n  주요 지표:")
        print(f"    전진 패스 비율: {profile['forward_pass_ratio']:.2%}")
        print(f"    롱패스 비율: {profile['long_pass_ratio']:.2%}")
        print(f"    패스 성공률: {profile['pass_success_rate']:.2%}")
        print(f"    평균 패스 거리: {profile['average_pass_length']:.1f}m")
        print(f"    중앙 지역 터치 비율: {profile['touch_zone_central']:.2%}")
        print(f"    전진 지역 터치 비율: {profile['touch_zone_forward']:.2%}")
        print(f"    평균 터치 위치: ({profile['average_touch_x']:.1f}, {profile['average_touch_y']:.1f})")
        print(f"    수비 행동 빈도: {profile['defensive_action_frequency']:.2%}")
        print(f"    패스 빈도: {profile['pass_frequency']:.2%}")
    
    return results

def analyze_comparison(results):
    """비교 분석 및 결론 도출"""
    print("\n" + "="*80)
    print("비교 분석 및 결론")
    print("="*80)
    
    if len(results) < 2:
        print("비교할 선수가 부족합니다.")
        return
    
    # 적합도 순위
    sorted_results = sorted(results, key=lambda x: x['fit_score'] if x['fit_score'] else 0, reverse=True)
    
    print("\n[딥라잉 플레이메이커 적합도 순위]")
    for i, result in enumerate(sorted_results, 1):
        print(f"  {i}. {result['name']} ({result['position']}): {result['fit_score']:.3f}")
    
    # 핵심 지표 비교
    print("\n[핵심 지표 비교]")
    key_metrics = ['long_pass_ratio', 'average_pass_length', 'average_touch_y', 'pass_success_rate', 'pass_frequency']
    
    for metric in key_metrics:
        print(f"\n  {metric}:")
        for result in sorted_results:
            value = result['profile'].get(metric, 0)
            if metric == 'average_pass_length':
                print(f"    {result['name']}: {value:.1f}m")
            elif metric == 'average_touch_y':
                print(f"    {result['name']}: {value:.1f}")
            else:
                print(f"    {result['name']}: {value:.2%}")
    
    # 박진섭과 CM 선수들 비교
    park_result = next((r for r in results if r['name'] == '박진섭'), None)
    cm_results = [r for r in results if r['position'] == 'CM']
    
    if park_result and len(cm_results) > 0:
        print("\n" + "="*80)
        print("박진섭 (CB) vs CM 선수들 비교")
        print("="*80)
        
        cm_avg_profile = {}
        for metric in key_metrics:
            cm_values = [r['profile'].get(metric, 0) for r in cm_results]
            cm_avg_profile[metric] = np.mean(cm_values)
        
        print("\n[CM 선수 평균 vs 박진섭]")
        for metric in key_metrics:
            park_value = park_result['profile'].get(metric, 0)
            cm_avg = cm_avg_profile[metric]
            diff = park_value - cm_avg
            diff_pct = (diff / cm_avg * 100) if cm_avg > 0 else 0
            
            if metric == 'average_pass_length':
                print(f"  {metric}:")
                print(f"    CM 평균: {cm_avg:.1f}m")
                print(f"    박진섭: {park_value:.1f}m (차이: {diff:+.1f}m, {diff_pct:+.1f}%)")
            elif metric == 'average_touch_y':
                print(f"  {metric}:")
                print(f"    CM 평균: {cm_avg:.1f}")
                print(f"    박진섭: {park_value:.1f} (차이: {diff:+.1f}, {diff_pct:+.1f}%)")
            else:
                print(f"  {metric}:")
                print(f"    CM 평균: {cm_avg:.2%}")
                print(f"    박진섭: {park_value:.2%} (차이: {diff:+.2%}, {diff_pct:+.1f}%)")
    
    # 결론 도출
    print("\n" + "="*80)
    print("결론")
    print("="*80)
    
    # 1. CM 선수들이 딥라잉 플레이메이커인가?
    cm_fit_scores = [r['fit_score'] for r in cm_results if r['fit_score']]
    if cm_fit_scores:
        cm_avg_fit = np.mean(cm_fit_scores)
        print(f"\n1. CM 선수들 (기성용, 정우영, 윤빛가람)의 딥라잉 플레이메이커 적합도:")
        print(f"   평균: {cm_avg_fit:.3f}")
        if cm_avg_fit > 0.95:
            print("   → 매우 높은 적합도. 이들은 딥라잉 플레이메이커로 분류 가능.")
        elif cm_avg_fit > 0.90:
            print("   → 높은 적합도. 이들은 딥라잉 플레이메이커 특성을 가짐.")
        else:
            print("   → 중간 적합도. 일부 특성만 일치.")
    
    # 2. 박진섭이 딥라잉 플레이메이커인가?
    if park_result:
        park_fit = park_result['fit_score']
        print(f"\n2. 박진섭 (CB)의 딥라잉 플레이메이커 적합도: {park_fit:.3f}")
        
        if park_fit and cm_fit_scores:
            park_rank = sum(1 for score in cm_fit_scores if score > park_fit) + 1
            total_players = len(cm_fit_scores) + 1
            print(f"   CM 선수들과 비교 시 순위: {park_rank}/{total_players}")
            
            if park_fit > np.mean(cm_fit_scores):
                print("   → 박진섭의 적합도가 CM 선수 평균보다 높음.")
                print("   → CB 포지션이지만 딥라잉 플레이메이커처럼 플레이한다고 볼 수 있음.")
            elif park_fit > np.mean(cm_fit_scores) - 0.05:
                print("   → 박진섭의 적합도가 CM 선수 평균과 비슷함.")
                print("   → CB 포지션이지만 딥라잉 플레이메이커 특성을 가진다고 볼 수 있음.")
            else:
                print("   → 박진섭의 적합도가 CM 선수 평균보다 낮음.")
                print("   → CB 포지션의 특성이 더 강하게 나타남.")
        
        # 핵심 지표 비교
        print(f"\n3. 핵심 지표 비교:")
        similar_metrics = []
        different_metrics = []
        
        for metric in key_metrics:
            park_value = park_result['profile'].get(metric, 0)
            if metric in cm_avg_profile:
                cm_avg = cm_avg_profile[metric]
                diff_pct = abs((park_value - cm_avg) / cm_avg * 100) if cm_avg > 0 else 0
                if diff_pct < 10:  # 10% 이내 차이
                    similar_metrics.append(metric)
                else:
                    different_metrics.append((metric, diff_pct))
        
        if similar_metrics:
            print(f"   박진섭과 CM 선수들이 유사한 지표:")
            for metric in similar_metrics:
                print(f"     - {metric}")
        
        if different_metrics:
            print(f"   박진섭과 CM 선수들이 다른 지표:")
            for metric, diff_pct in different_metrics:
                print(f"     - {metric} (차이: {diff_pct:.1f}%)")
    
    print("\n[최종 결론]")
    if park_result and cm_fit_scores:
        if park_result['fit_score'] > np.mean(cm_fit_scores):
            print("✓ 박진섭은 CB 포지션이지만, 딥라잉 플레이메이커처럼 플레이한다고 볼 수 있습니다.")
            print("  적합도가 CM 선수들 평균보다 높으며, 핵심 지표에서도 유사한 패턴을 보입니다.")
        elif park_result['fit_score'] > np.mean(cm_fit_scores) - 0.05:
            print("△ 박진섭은 CB 포지션이지만, 일부 딥라잉 플레이메이커 특성을 가집니다.")
            print("  적합도가 CM 선수들과 비슷하며, 특정 지표에서 유사한 패턴을 보입니다.")
        else:
            print("✗ 박진섭은 CB 포지션의 특성이 더 강하게 나타납니다.")
            print("  적합도가 CM 선수들보다 낮으며, 핵심 지표에서 차이가 있습니다.")

def main():
    df, match_info_df = load_data()
    
    # 선수 정보
    players = {
        '기성용': 161110.0,
        '정우영': 529466.0,
        '윤빛가람': 354812.0,
        '박진섭': 246402.0
    }
    
    player_ids = list(players.values())
    player_names = list(players.keys())
    
    # 비교 분석
    results = compare_players(df, player_ids, player_names)
    
    # 결론 도출
    analyze_comparison(results)

if __name__ == '__main__':
    main()


"""
롤 기반 선수 비교 및 레이더 차트 생성

목적:
1. 특정 롤(예: 딥라잉 플레이메이커)에 속한 선수들 식별
2. 행동 프로파일 기반 성과 지표로 랭킹
3. 특정 선수가 해당 롤의 상위 선수들과 비교한 레이더 차트 생성
"""

import pandas as pd
import numpy as np
from pathlib import Path
from scipy.spatial.distance import cosine
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
from math import pi

# 한글 폰트 설정
plt.rcParams['font.family'] = 'AppleGothic'  # macOS
plt.rcParams['axes.unicode_minus'] = False

PROJECT_ROOT = Path(__file__).parent.parent

def load_data():
    """데이터 로딩"""
    df = pd.read_csv(PROJECT_ROOT / 'raw_data' / 'open_track2' / 'raw_data.csv')
    match_info_df = pd.read_csv(PROJECT_ROOT / 'raw_data' / 'open_track2' / 'match_info.csv')
    return df, match_info_df

def calculate_player_profile(df, player_id):
    """선수별 행동 프로파일 계산"""
    player_data = df[df['player_id'] == player_id].copy()
    
    if len(player_data) < 50:  # 최소 이벤트 수 체크
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
        
        # 전진 패스 성공률
        forward_successful = forward_passes[forward_passes['result_name'] == 'Successful']
        profile['forward_pass_success_rate'] = len(forward_successful) / len(forward_passes) if len(forward_passes) > 0 else 0
    else:
        profile['forward_pass_ratio'] = 0
        profile['long_pass_ratio'] = 0
        profile['pass_success_rate'] = 0
        profile['average_pass_length'] = 0
        profile['forward_pass_success_rate'] = 0
    
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
    
    # 빌드업 참여도
    profile['pass_frequency'] = len(passes) / len(player_data)
    profile['event_frequency'] = len(player_data)
    
    # 경기당 평균 지표 (정규화)
    games = player_data['game_id'].nunique()
    profile['passes_per_game'] = len(passes) / games if games > 0 else 0
    profile['events_per_game'] = len(player_data) / games if games > 0 else 0
    
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
            'pass_frequency': 0.3,
        },
    }
    return templates.get(role_name, {})

def calculate_role_fit_score(player_profile, role_template):
    """롤 적합도 스코어 계산"""
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

def calculate_performance_score(player_profile, role_name):
    """
    행동 프로파일 기반 성과 지표 계산
    
    딥라잉 플레이메이커의 경우:
    - 패스 성공률 (높을수록 좋음)
    - 롱패스 비율 (높을수록 좋음)
    - 전진 패스 성공률 (높을수록 좋음)
    - 경기당 패스 수 (높을수록 좋음)
    - 빌드업 참여도 (높을수록 좋음)
    """
    if player_profile is None:
        return None
    
    if role_name == '딥라잉 플레이메이커':
        # 가중 평균으로 성과 점수 계산
        performance_score = (
            player_profile.get('pass_success_rate', 0) * 0.3 +
            player_profile.get('long_pass_ratio', 0) * 0.2 +
            player_profile.get('forward_pass_success_rate', 0) * 0.2 +
            min(player_profile.get('passes_per_game', 0) / 50, 1.0) * 0.15 +  # 정규화 (50개 이상이면 1.0)
            player_profile.get('pass_frequency', 0) * 0.15
        )
        return performance_score
    
    return None

def find_players_by_role(df, role_name, min_events=100):
    """
    특정 롤에 속한 선수들 찾기
    
    반환: [(player_id, player_name, position, team, fit_score, performance_score), ...]
    """
    print(f"\n{'='*80}")
    print(f"{role_name} 롤에 속한 선수 찾기")
    print(f"{'='*80}")
    
    role_template = define_role_template(role_name)
    if not role_template:
        print(f"❌ 롤 템플릿이 정의되지 않았습니다: {role_name}")
        return []
    
    player_ids = df['player_id'].dropna().unique()
    results = []
    
    print(f"총 {len(player_ids)}명의 선수 중 검색 중...")
    
    for player_id in player_ids:
        player_data = df[df['player_id'] == player_id]
        
        if len(player_data) < min_events:
            continue
        
        profile = calculate_player_profile(df, player_id)
        if profile is None:
            continue
        
        fit_score = calculate_role_fit_score(profile, role_template)
        if fit_score is None:
            continue
        
        performance_score = calculate_performance_score(profile, role_name)
        if performance_score is None:
            continue
        
        player_name = player_data['player_name_ko'].iloc[0]
        position = player_data['main_position'].iloc[0]
        team = player_data['team_name_ko'].iloc[0]
        
        results.append({
            'player_id': player_id,
            'player_name': player_name,
            'position': position,
            'team': team,
            'fit_score': fit_score,
            'performance_score': performance_score,
            'profile': profile
        })
    
    # 적합도와 성과 점수로 정렬 (가중 평균)
    for result in results:
        result['combined_score'] = result['fit_score'] * 0.5 + result['performance_score'] * 0.5
    
    results.sort(key=lambda x: x['combined_score'], reverse=True)
    
    print(f"\n✓ {len(results)}명의 선수를 찾았습니다.")
    
    return results

def create_radar_chart(player_profiles, player_names, metrics, title, output_path):
    """
    레이더 차트 생성
    
    player_profiles: [profile1, profile2, ...] 리스트
    player_names: ['선수1', '선수2', ...] 리스트
    metrics: ['metric1', 'metric2', ...] 리스트 (표시할 지표)
    """
    # 각 지표별 최대값 찾기 (정규화용)
    max_values = {}
    for metric in metrics:
        max_val = max([p.get(metric, 0) for p in player_profiles])
        max_values[metric] = max_val if max_val > 0 else 1
    
    # 각도 계산
    angles = [n / float(len(metrics)) * 2 * pi for n in range(len(metrics))]
    angles += angles[:1]  # 원형으로 만들기 위해
    
    fig, ax = plt.subplots(figsize=(12, 12), subplot_kw=dict(projection='polar'))
    
    colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd', '#8c564b']
    
    for idx, (profile, name) in enumerate(zip(player_profiles, player_names)):
        values = []
        for metric in metrics:
            value = profile.get(metric, 0)
            # 정규화 (0~1 범위)
            normalized_value = value / max_values[metric] if max_values[metric] > 0 else 0
            values.append(normalized_value)
        
        values += values[:1]  # 원형으로 만들기
        
        ax.plot(angles, values, 'o-', linewidth=2, label=name, color=colors[idx % len(colors)])
        ax.fill(angles, values, alpha=0.15, color=colors[idx % len(colors)])
    
    # 축 레이블 설정
    metric_labels = {
        'pass_success_rate': '패스 성공률',
        'long_pass_ratio': '롱패스 비율',
        'forward_pass_success_rate': '전진 패스 성공률',
        'passes_per_game': '경기당 패스 수',
        'pass_frequency': '패스 빈도',
        'average_pass_length': '평균 패스 거리',
        'touch_zone_central': '중앙 지역 터치',
        'average_touch_y': '평균 터치 Y 위치',
    }
    
    ax.set_xticks(angles[:-1])
    ax.set_xticklabels([metric_labels.get(m, m) for m in metrics], fontsize=11)
    ax.set_ylim(0, 1)
    ax.set_yticks([0.2, 0.4, 0.6, 0.8, 1.0])
    ax.set_yticklabels(['0.2', '0.4', '0.6', '0.8', '1.0'], fontsize=9)
    ax.grid(True)
    
    plt.legend(loc='upper right', bbox_to_anchor=(1.3, 1.1), fontsize=10)
    plt.title(title, size=14, fontweight='bold', pad=20)
    
    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    print(f"✓ 레이더 차트 저장: {output_path}")
    plt.close()

def compare_player_with_top_players(df, target_player_id, role_name, top_n=5):
    """
    특정 선수를 해당 롤의 상위 선수들과 비교
    
    반환: 비교 결과 및 레이더 차트
    """
    print(f"\n{'='*80}")
    print(f"선수 비교 분석: {role_name}")
    print(f"{'='*80}")
    
    # 1. 해당 롤에 속한 모든 선수 찾기
    all_players = find_players_by_role(df, role_name)
    
    if len(all_players) == 0:
        print("❌ 해당 롤에 속한 선수를 찾을 수 없습니다.")
        return None
    
    # 2. 타겟 선수 찾기
    target_player = None
    for player in all_players:
        if player['player_id'] == target_player_id:
            target_player = player
            break
    
    if target_player is None:
        print(f"❌ 타겟 선수 (player_id={target_player_id})를 해당 롤 선수 목록에서 찾을 수 없습니다.")
        return None
    
    # 3. 상위 N명 선수 선택
    top_players = all_players[:top_n]
    
    print(f"\n[비교 대상]")
    print(f"타겟 선수: {target_player['player_name']} ({target_player['position']}, {target_player['team']})")
    print(f"  적합도: {target_player['fit_score']:.3f}")
    print(f"  성과 점수: {target_player['performance_score']:.3f}")
    print(f"  종합 점수: {target_player['combined_score']:.3f}")
    print(f"  랭킹: {all_players.index(target_player) + 1}/{len(all_players)}")
    
    print(f"\n상위 {top_n}명 선수:")
    for i, player in enumerate(top_players, 1):
        print(f"  {i}. {player['player_name']} ({player['position']}, {player['team']})")
        print(f"     적합도: {player['fit_score']:.3f}, 성과: {player['performance_score']:.3f}, 종합: {player['combined_score']:.3f}")
    
    # 4. 레이더 차트 생성
    player_profiles = [target_player['profile']] + [p['profile'] for p in top_players]
    player_names = [target_player['player_name']] + [p['player_name'] for p in top_players]
    
    # 딥라잉 플레이메이커 핵심 지표
    if role_name == '딥라잉 플레이메이커':
        metrics = [
            'pass_success_rate',
            'long_pass_ratio',
            'forward_pass_success_rate',
            'passes_per_game',
            'pass_frequency',
            'average_pass_length',
            'touch_zone_central',
            'average_touch_y'
        ]
    
    output_path = PROJECT_ROOT / 'analysis' / f'radar_{role_name.replace(" ", "_")}_{target_player["player_name"]}.png'
    create_radar_chart(
        player_profiles,
        player_names,
        metrics,
        f'{role_name} 비교: {target_player["player_name"]} vs 상위 {top_n}명',
        output_path
    )
    
    return {
        'target_player': target_player,
        'top_players': top_players,
        'all_players': all_players,
        'ranking': all_players.index(target_player) + 1,
        'total_players': len(all_players)
    }

def main():
    """메인 실행 함수"""
    print("="*80)
    print("롤 기반 선수 비교 분석")
    print("="*80)
    
    df, match_info_df = load_data()
    
    # 예시: 박진섭 선수를 딥라잉 플레이메이커 상위 선수들과 비교
    target_player_id = 246402.0  # 박진섭
    role_name = '딥라잉 플레이메이커'
    
    result = compare_player_with_top_players(df, target_player_id, role_name, top_n=5)
    
    if result:
        print(f"\n{'='*80}")
        print("분석 완료")
        print(f"{'='*80}")
        print(f"\n결과 요약:")
        print(f"- {role_name} 롤에 속한 선수: {result['total_players']}명")
        print(f"- 타겟 선수 랭킹: {result['ranking']}/{result['total_players']}")
        print(f"- 레이더 차트: analysis/radar_{role_name.replace(' ', '_')}_{result['target_player']['player_name']}.png")

if __name__ == '__main__':
    main()


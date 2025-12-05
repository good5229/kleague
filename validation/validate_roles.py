"""
롤 정의 검증 스크립트

목적: PLAN.md에서 정의한 롤(예: "딥라잉 플레이메이커")이 실제로 해당 롤을 수행하는 선수를
      올바르게 식별하는지 검증

검증 방법:
1. 알려진 롤을 가진 선수들을 테스트 케이스로 사용 (외부 지식 기반)
2. 우리가 계산한 행동 프로파일이 해당 롤의 기대 패턴과 일치하는지 확인
3. 롤별 대표 지표의 분포를 시각화하여 해석 가능성 확인

주의: 이 검증은 "도메인 전문가 검토"가 필요합니다. 실제 축구 지식과 비교하여
      롤 정의와 지표 가중치를 조정해야 할 수 있습니다.
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
from scipy.spatial.distance import cosine

# 프로젝트 루트 경로
PROJECT_ROOT = Path(__file__).parent.parent

def load_data():
    """데이터 로딩"""
    df = pd.read_csv(PROJECT_ROOT / 'raw_data' / 'open_track2' / 'raw_data.csv')
    match_info_df = pd.read_csv(PROJECT_ROOT / 'raw_data' / 'open_track2' / 'match_info.csv')
    return df, match_info_df

def calculate_player_profile(df, player_id):
    """
    선수별 행동 프로파일 계산
    
    반환: 딕셔너리 형태의 프로파일 벡터
    """
    player_data = df[df['player_id'] == player_id].copy()
    
    if len(player_data) < 50:  # 최소 이벤트 수 체크
        return None
    
    profile = {}
    
    # 패스 관련 지표
    passes = player_data[player_data['type_name'] == 'Pass']
    if len(passes) > 0:
        # 전진 패스 비율
        forward_passes = passes[passes['dx'] > 0]
        profile['forward_pass_ratio'] = len(forward_passes) / len(passes)
        
        # 롱패스 비율 (거리 > 20m)
        pass_lengths = np.sqrt(passes['dx']**2 + passes['dy']**2)
        long_passes = (pass_lengths > 20).sum()
        profile['long_pass_ratio'] = long_passes / len(passes)
        
        # 패스 성공률
        successful_passes = passes[passes['result_name'] == 'Successful']
        profile['pass_success_rate'] = len(successful_passes) / len(passes)
        
        # 평균 패스 거리
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
    """
    롤 템플릿 정의 (기대 행동 패턴)
    
    주의: 이 정의는 PLAN.md의 설명을 바탕으로 한 초안입니다.
          실제 축구 도메인 지식과 비교하여 검증 및 조정이 필요합니다.
    """
    templates = {
        '딥라잉 플레이메이커': {
            'forward_pass_ratio': 0.6,  # 높음 (전진 패스 많이)
            'long_pass_ratio': 0.4,     # 높음 (롱패스 자주)
            'pass_success_rate': 0.85,  # 높음 (정확한 패스)
            'average_pass_length': 15,   # 중간-높음
            'touch_zone_central': 0.7,  # 높음 (중앙 지역)
            'touch_zone_forward': 0.3,  # 낮음 (수비 라인 근처)
            'average_touch_x': 50,      # 중앙
            'average_touch_y': 30,      # 후방
            'defensive_action_frequency': 0.05,  # 낮음 (공격 지향)
            'shot_frequency': 0.01,     # 낮음 (슈팅 적음)
        },
        '인벌빙 풀백': {
            'forward_pass_ratio': 0.5,  # 중간
            'long_pass_ratio': 0.2,     # 낮음
            'pass_success_rate': 0.80,  # 중간
            'average_pass_length': 10,  # 짧음
            'touch_zone_central': 0.4,  # 중간 (중앙도 가지만)
            'touch_zone_wide': 0.6,     # 높음 (측면)
            'touch_zone_forward': 0.5,  # 높음 (전진)
            'average_touch_x': 30,      # 측면 (또는 70)
            'average_touch_y': 50,      # 중앙-전진
            'defensive_action_frequency': 0.10,  # 중간
            'shot_frequency': 0.02,     # 중간
        },
        '박스투박스 미드필더': {
            'forward_pass_ratio': 0.55,  # 중간-높음
            'long_pass_ratio': 0.25,     # 중간
            'pass_success_rate': 0.82,   # 중간-높음
            'average_pass_length': 12,   # 중간
            'touch_zone_central': 0.6,   # 높음
            'touch_zone_forward': 0.4,   # 중간
            'average_touch_x': 50,       # 중앙
            'average_touch_y': 40,       # 중앙
            'defensive_action_frequency': 0.15,  # 높음 (수비도 함)
            'shot_frequency': 0.03,      # 중간
        },
    }
    
    return templates.get(role_name, {})

def calculate_role_fit_score(player_profile, role_template):
    """
    선수 프로파일과 롤 템플릿 간의 적합도 스코어 계산 (코사인 유사도)
    
    주의: 모든 지표를 동일한 가중치로 계산합니다.
          실제로는 포지션별로 중요 지표에 가중치를 부여해야 할 수 있습니다.
    """
    if player_profile is None or not role_template:
        return None
    
    # 벡터로 변환 (템플릿에 있는 지표만 사용)
    player_vector = []
    template_vector = []
    
    for key in role_template.keys():
        if key in player_profile:
            player_vector.append(player_profile[key])
            template_vector.append(role_template[key])
    
    if len(player_vector) == 0:
        return None
    
    # 정규화 (0~1 범위로)
    player_vector = np.array(player_vector)
    template_vector = np.array(template_vector)
    
    # 코사인 유사도 계산
    # 1 - cosine distance = similarity (0~1, 1에 가까울수록 유사)
    try:
        cosine_sim = 1 - cosine(player_vector, template_vector)
        return cosine_sim
    except:
        return None

def validate_role_definition(df, role_name, test_cases=None):
    """
    롤 정의 검증
    
    test_cases: {player_id: expected_role} 형태의 딕셔너리
                (예: {356618: '딥라잉 플레이메이커'})
                None이면 모든 선수에 대해 롤 적합도를 계산하여 분포 확인
    """
    print(f"\n{'='*60}")
    print(f"롤 정의 검증: {role_name}")
    print(f"{'='*60}")
    
    role_template = define_role_template(role_name)
    if not role_template:
        print(f"❌ 롤 템플릿이 정의되지 않았습니다: {role_name}")
        return None
    
    print(f"\n롤 템플릿 (기대 패턴):")
    for key, value in role_template.items():
        print(f"  {key}: {value}")
    
    # 모든 선수에 대해 적합도 계산
    player_ids = df['player_id'].dropna().unique()
    fit_scores = []
    player_profiles = []
    
    print(f"\n선수별 적합도 계산 중... (총 {len(player_ids)}명)")
    
    for player_id in player_ids[:100]:  # 샘플링 (처음 100명만, 전체는 시간이 오래 걸림)
        profile = calculate_player_profile(df, player_id)
        if profile:
            fit_score = calculate_role_fit_score(profile, role_template)
            if fit_score is not None:
                fit_scores.append(fit_score)
                player_profiles.append({
                    'player_id': player_id,
                    'fit_score': fit_score,
                    'profile': profile
                })
    
    if len(fit_scores) == 0:
        print("❌ 적합도 계산 결과가 없습니다.")
        return None
    
    # 통계 요약
    print(f"\n[적합도 스코어 통계]")
    print(f"  평균: {np.mean(fit_scores):.3f}")
    print(f"  표준편차: {np.std(fit_scores):.3f}")
    print(f"  최소: {np.min(fit_scores):.3f}")
    print(f"  최대: {np.max(fit_scores):.3f}")
    print(f"  중앙값: {np.median(fit_scores):.3f}")
    
    # 상위 적합도 선수들
    sorted_players = sorted(player_profiles, key=lambda x: x['fit_score'], reverse=True)
    print(f"\n[상위 5명 적합도]")
    for i, player in enumerate(sorted_players[:5], 1):
        player_id = player['player_id']
        player_name = df[df['player_id'] == player_id]['player_name_ko'].iloc[0] if len(df[df['player_id'] == player_id]) > 0 else 'N/A'
        position = df[df['player_id'] == player_id]['main_position'].iloc[0] if len(df[df['player_id'] == player_id]) > 0 else 'N/A'
        print(f"  {i}. player_id={player_id}, 이름={player_name}, 포지션={position}, 적합도={player['fit_score']:.3f}")
    
    # 테스트 케이스가 있으면 검증
    if test_cases:
        print(f"\n[테스트 케이스 검증]")
        for player_id, expected_role in test_cases.items():
            if expected_role != role_name:
                continue
            profile = calculate_player_profile(df, player_id)
            if profile:
                fit_score = calculate_role_fit_score(profile, role_template)
                player_name = df[df['player_id'] == player_id]['player_name_ko'].iloc[0] if len(df[df['player_id'] == player_id]) > 0 else 'N/A'
                status = "✓" if fit_score and fit_score > np.median(fit_scores) else "⚠"
                print(f"  {status} {player_name} (player_id={player_id}): 적합도={fit_score:.3f if fit_score else 'N/A'}")
    
    return {
        'fit_scores': fit_scores,
        'player_profiles': player_profiles,
        'role_template': role_template
    }

def visualize_role_distribution(validation_results, role_name):
    """롤 적합도 분포 시각화"""
    if not validation_results:
        return
    
    fit_scores = validation_results['fit_scores']
    
    plt.figure(figsize=(10, 6))
    plt.hist(fit_scores, bins=20, edgecolor='black', alpha=0.7)
    plt.axvline(np.mean(fit_scores), color='red', linestyle='--', label=f'평균: {np.mean(fit_scores):.3f}')
    plt.axvline(np.median(fit_scores), color='green', linestyle='--', label=f'중앙값: {np.median(fit_scores):.3f}')
    plt.xlabel('적합도 스코어 (코사인 유사도)')
    plt.ylabel('선수 수')
    plt.title(f'{role_name} 롤 적합도 분포')
    plt.legend()
    plt.grid(alpha=0.3)
    
    output_path = PROJECT_ROOT / 'validation' / f'role_fit_{role_name.replace(" ", "_")}.png'
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    print(f"\n✓ 분포 그래프 저장: {output_path}")
    plt.close()

def main():
    """메인 실행 함수"""
    print("\n" + "="*60)
    print("롤 정의 검증 스크립트")
    print("="*60)
    print("\n주의: 이 검증은 '도메인 전문가 검토'가 필요합니다.")
    print("실제 축구 지식과 비교하여 롤 정의와 지표 가중치를 조정해야 할 수 있습니다.\n")
    
    df, match_info_df = load_data()
    
    # 검증할 롤들
    roles_to_validate = ['딥라잉 플레이메이커', '인벌빙 풀백', '박스투박스 미드필더']
    
    # 테스트 케이스 (실제로 알려진 롤을 가진 선수들)
    # 주의: 이 부분은 축구 전문가나 팬 커뮤니티의 지식을 바탕으로 채워야 합니다.
    # 현재는 예시로만 두고, 실제 검증 시 채워넣어야 합니다.
    test_cases = {
        # 예시: {player_id: '딥라잉 플레이메이커'}
        # 실제로는 알려진 선수들의 player_id를 찾아서 입력해야 함
    }
    
    all_results = {}
    
    for role_name in roles_to_validate:
        result = validate_role_definition(df, role_name, test_cases)
        if result:
            all_results[role_name] = result
            visualize_role_distribution(result, role_name)
    
    # 최종 요약
    print("\n" + "="*60)
    print("검증 요약 및 권장사항")
    print("="*60)
    print("\n[검증 완료된 롤]")
    for role_name in all_results.keys():
        print(f"  ✓ {role_name}")
    
    print("\n[다음 단계 권장사항]")
    print("1. 실제 축구 전문가/팬 커뮤니티에서 '딥라잉 플레이메이커'로 알려진 선수들의")
    print("   player_id를 찾아 test_cases에 추가하여 검증")
    print("2. 상위 적합도 선수들의 실제 경기 영상/해설을 확인하여 롤 정의가 맞는지 검토")
    print("3. 롤 템플릿의 지표 가중치를 조정 (현재는 모든 지표를 동일 가중치로 계산)")
    print("4. 포지션별로 중요 지표가 다를 수 있으므로, 포지션별 롤 템플릿 분리 고려")
    print("\n주의: 이 검증 결과만으로 롤 정의가 완벽하다고 판단할 수 없습니다.")
    print("      도메인 전문가의 검토와 실제 경기 관찰이 필요합니다.")

if __name__ == '__main__':
    main()


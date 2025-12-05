"""
데이터 기반 롤 정의

목적: 실제 데이터에서 각 포지션별 선수들의 행동 프로파일을 계산하고,
      클러스터링을 통해 포지션 내 롤을 구분하여 객관적인 롤 템플릿 정의

근거: 실제 선수 행동 데이터 기반 (추정치 없음)
"""

import pandas as pd
import numpy as np
from pathlib import Path
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
import json

PROJECT_ROOT = Path(__file__).parent.parent

def load_data():
    df = pd.read_csv(PROJECT_ROOT / 'raw_data' / 'open_track2' / 'raw_data.csv')
    match_info_df = pd.read_csv(PROJECT_ROOT / 'raw_data' / 'open_track2' / 'match_info.csv')
    return df, match_info_df

def calculate_comprehensive_profile(df, player_id):
    """선수별 종합 행동 프로파일 계산 (모든 지표 포함)"""
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
        very_long_passes = (pass_lengths > 30).sum()
        short_passes = (pass_lengths <= 10).sum()
        
        profile['long_pass_ratio'] = long_passes / len(passes)
        profile['very_long_pass_ratio'] = very_long_passes / len(passes)
        profile['short_pass_ratio'] = short_passes / len(passes)
        profile['average_pass_length'] = pass_lengths.mean()
        
        successful_passes = passes[passes['result_name'] == 'Successful']
        profile['pass_success_rate'] = len(successful_passes) / len(passes)
        
        # 전방 패스
        forward_passes = passes[passes['end_y'] > passes['start_y']]
        if len(forward_passes) > 0:
            forward_successful = forward_passes[forward_passes['result_name'] == 'Successful']
            profile['forward_pass_success_rate'] = len(forward_successful) / len(forward_passes)
            forward_distances = np.sqrt(
                (forward_passes['end_x'] - forward_passes['start_x'])**2 +
                (forward_passes['end_y'] - forward_passes['start_y'])**2
            )
            profile['average_forward_pass_distance'] = forward_distances.mean()
        else:
            profile['forward_pass_success_rate'] = 0
            profile['average_forward_pass_distance'] = 0
    else:
        profile['forward_pass_ratio'] = 0
        profile['long_pass_ratio'] = 0
        profile['very_long_pass_ratio'] = 0
        profile['short_pass_ratio'] = 0
        profile['average_pass_length'] = 0
        profile['pass_success_rate'] = 0
        profile['forward_pass_success_rate'] = 0
        profile['average_forward_pass_distance'] = 0
    
    # 캐리 관련
    carries = player_data[player_data['type_name'] == 'Carry']
    if len(carries) > 0:
        carry_lengths = np.sqrt(carries['dx']**2 + carries['dy']**2)
        profile['average_carry_length'] = carry_lengths.mean()
        profile['carry_frequency'] = len(carries) / len(player_data)
    else:
        profile['average_carry_length'] = 0
        profile['carry_frequency'] = 0
    
    # 공간 활용
    profile['average_touch_x'] = player_data['start_x'].mean()
    profile['average_touch_y'] = player_data['start_y'].mean()
    profile['touch_zone_central'] = ((player_data['start_x'] >= 30) & (player_data['start_x'] <= 70)).sum() / len(player_data)
    profile['touch_zone_wide'] = ((player_data['start_x'] < 30) | (player_data['start_x'] > 70)).sum() / len(player_data)
    profile['touch_zone_defensive'] = (player_data['start_y'] < 30).sum() / len(player_data)
    profile['touch_zone_midfield'] = ((player_data['start_y'] >= 30) & (player_data['start_y'] < 50)).sum() / len(player_data)
    profile['touch_zone_forward'] = (player_data['start_y'] >= 50).sum() / len(player_data)
    
    # 수비 행동
    interventions = player_data[player_data['type_name'] == 'Intervention']
    blocks = player_data[player_data['type_name'] == 'Block']
    tackles = player_data[player_data['type_name'] == 'Tackle']
    clearances = player_data[player_data['type_name'] == 'Clearance']
    
    profile['defensive_action_frequency'] = (len(interventions) + len(blocks)) / len(player_data)
    profile['tackle_frequency'] = len(tackles) / len(player_data)
    profile['clearance_frequency'] = len(clearances) / len(player_data)
    
    # 공격 행동
    shots = player_data[player_data['type_name'] == 'Shot']
    profile['shot_frequency'] = len(shots) / len(player_data)
    
    # 빌드업 참여
    profile['pass_frequency'] = len(passes) / len(player_data)
    pass_received = player_data[player_data['type_name'] == 'Pass Received']
    profile['pass_received_frequency'] = len(pass_received) / len(player_data)
    
    # 경기당 지표
    games = player_data['game_id'].nunique()
    profile['passes_per_game'] = len(passes) / games if games > 0 else 0
    profile['events_per_game'] = len(player_data) / games if games > 0 else 0
    
    return profile

def cluster_players_by_role(df, position, n_clusters=3, min_events=100):
    """
    포지션별 선수들을 클러스터링하여 롤 구분
    
    반환: {cluster_id: {'players': [...], 'template': {...}}}
    """
    position_players = df[df['main_position'] == position]
    player_ids = position_players['player_id'].dropna().unique()
    
    profiles = []
    valid_player_ids = []
    
    for player_id in player_ids:
        profile = calculate_comprehensive_profile(df, player_id)
        if profile and len(position_players[position_players['player_id'] == player_id]) >= min_events:
            profiles.append(profile)
            valid_player_ids.append(player_id)
    
    if len(profiles) < n_clusters:
        print(f"⚠ {position}: 선수 수({len(profiles)})가 클러스터 수({n_clusters})보다 적습니다.")
        return None
    
    # 프로파일을 데이터프레임으로 변환
    profile_df = pd.DataFrame(profiles)
    
    # 클러스터링에 사용할 핵심 지표 선택 (포지션별로 다를 수 있음)
    # 모든 지표 사용 (정규화 필요)
    feature_cols = [col for col in profile_df.columns if col not in ['passes_per_game', 'events_per_game']]
    
    if len(feature_cols) == 0:
        return None
    
    X = profile_df[feature_cols].values
    
    # 정규화
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)
    
    # KMeans 클러스터링
    kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
    clusters = kmeans.fit_predict(X_scaled)
    
    # 클러스터별 결과 정리
    result = {}
    for cluster_id in range(n_clusters):
        cluster_indices = np.where(clusters == cluster_id)[0]
        cluster_profiles = [profiles[i] for i in cluster_indices]
        cluster_player_ids = [valid_player_ids[i] for i in cluster_indices]
        
        # 클러스터 평균 프로파일 (롤 템플릿)
        cluster_template = {}
        for key in feature_cols:
            values = [p.get(key, 0) for p in cluster_profiles]
            cluster_template[key] = np.mean(values)
        
        result[cluster_id] = {
            'player_ids': cluster_player_ids,
            'player_count': len(cluster_player_ids),
            'template': cluster_template
        }
    
    return result, profile_df, feature_cols

def define_roles_for_all_positions(df):
    """모든 포지션에 대해 롤 정의"""
    print("="*80)
    print("데이터 기반 롤 정의")
    print("="*80)
    print("\n근거: 실제 선수 행동 데이터 기반 클러스터링")
    print("레퍼런스: 없음 (순수 데이터 기반)\n")
    
    # 충분한 데이터가 있는 포지션만 처리
    position_counts = df.groupby('main_position')['player_id'].nunique().sort_values(ascending=False)
    valid_positions = position_counts[position_counts >= 10].index.tolist()  # 최소 10명 이상
    
    print(f"분석 대상 포지션: {valid_positions}\n")
    
    all_role_templates = {}
    
    for position in valid_positions:
        print(f"\n{'='*80}")
        print(f"{position} 포지션 롤 정의")
        print(f"{'='*80}")
        
        player_count = position_counts[position]
        print(f"선수 수: {player_count}명")
        
        # 클러스터 수 결정 (선수 수에 따라)
        if player_count >= 30:
            n_clusters = 3
        elif player_count >= 15:
            n_clusters = 2
        else:
            n_clusters = 1  # 롤 구분 불가
        
        if n_clusters == 1:
            print(f"⚠ 선수 수가 적어 롤 구분 불가. 포지션 평균만 계산합니다.")
            # 포지션 평균 프로파일 계산
            position_players = df[df['main_position'] == position]
            player_ids = position_players['player_id'].dropna().unique()
            
            profiles = []
            for player_id in player_ids:
                profile = calculate_comprehensive_profile(df, player_id)
                if profile:
                    profiles.append(profile)
            
            if len(profiles) > 0:
                template = {}
                for key in profiles[0].keys():
                    template[key] = np.mean([p.get(key, 0) for p in profiles])
                
                all_role_templates[position] = {
                    '롤_0': template
                }
            continue
        
        # 클러스터링 수행
        result = cluster_players_by_role(df, position, n_clusters=n_clusters)
        
        if result is None:
            continue
        
        clusters, profile_df, feature_cols = result
        
        print(f"\n클러스터링 결과 ({n_clusters}개 롤):")
        for cluster_id, cluster_data in clusters.items():
            print(f"\n  롤_{cluster_id}: {cluster_data['player_count']}명")
            
            # 대표 지표 출력
            template = cluster_data['template']
            print(f"    주요 지표:")
            key_metrics = ['forward_pass_ratio', 'long_pass_ratio', 'pass_success_rate', 
                          'average_touch_y', 'defensive_action_frequency', 'shot_frequency']
            for metric in key_metrics:
                if metric in template:
                    value = template[metric]
                    if 'ratio' in metric or 'frequency' in metric or 'zone' in metric:
                        print(f"      {metric}: {value:.2%}")
                    else:
                        print(f"      {metric}: {value:.2f}")
        
        # 롤 템플릿 저장
        position_roles = {}
        for cluster_id, cluster_data in clusters.items():
            position_roles[f'롤_{cluster_id}'] = cluster_data['template']
        
        all_role_templates[position] = position_roles
    
    return all_role_templates

def save_role_templates(templates, output_path):
    """롤 템플릿을 JSON 파일로 저장"""
    # JSON 직렬화를 위해 numpy 타입 변환
    def convert_numpy(obj):
        if isinstance(obj, np.integer):
            return int(obj)
        elif isinstance(obj, np.floating):
            return float(obj)
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        return obj
    
    def clean_dict(d):
        if isinstance(d, dict):
            return {k: clean_dict(v) for k, v in d.items()}
        elif isinstance(d, list):
            return [clean_dict(item) for item in d]
        else:
            return convert_numpy(d)
    
    cleaned_templates = clean_dict(templates)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(cleaned_templates, f, ensure_ascii=False, indent=2)
    
    print(f"\n✓ 롤 템플릿 저장: {output_path}")

def main():
    df, match_info_df = load_data()
    
    # 모든 포지션에 대해 롤 정의
    role_templates = define_roles_for_all_positions(df)
    
    # 결과 저장
    output_path = PROJECT_ROOT / 'analysis' / 'role_templates_data_based.json'
    save_role_templates(role_templates, output_path)
    
    print("\n" + "="*80)
    print("롤 정의 완료")
    print("="*80)
    print(f"\n총 {len(role_templates)}개 포지션에 대해 롤이 정의되었습니다.")
    print("각 롤 템플릿은 실제 선수 행동 데이터 기반 클러스터링으로 생성되었습니다.")
    print("\n주의: 이 롤들은 데이터 기반으로 자동 생성된 것이므로,")
    print("      실제 축구 도메인에서 사용되는 롤 이름과 다를 수 있습니다.")
    print("      필요시 도메인 전문가가 각 롤에 적절한 이름을 부여해야 합니다.")

if __name__ == '__main__':
    main()


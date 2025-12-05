"""
롤 클러스터링 결과 검증

목적: 클러스터링으로 생성된 롤들이 실제로 의미 있는 구분인지 검증
      (행동 강령: 실행 결과 검증 필수)
"""

import pandas as pd
import numpy as np
import json
from pathlib import Path
from scipy.stats import f_oneway

PROJECT_ROOT = Path(__file__).parent.parent

def load_data():
    df = pd.read_csv(PROJECT_ROOT / 'raw_data' / 'open_track2' / 'raw_data.csv')
    return df

def load_role_templates():
    """생성된 롤 템플릿 로딩"""
    template_path = PROJECT_ROOT / 'analysis' / 'role_templates_data_based.json'
    if not template_path.exists():
        return None
    
    with open(template_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def calculate_player_profile(df, player_id):
    """선수 프로파일 계산 (간단 버전)"""
    player_data = df[df['player_id'] == player_id].copy()
    if len(player_data) < 50:
        return None
    
    profile = {}
    passes = player_data[player_data['type_name'] == 'Pass']
    if len(passes) > 0:
        pass_lengths = np.sqrt(passes['dx']**2 + passes['dy']**2)
        profile['long_pass_ratio'] = (pass_lengths > 20).sum() / len(passes)
        profile['average_touch_y'] = player_data['start_y'].mean()
        profile['pass_success_rate'] = len(passes[passes['result_name'] == 'Successful']) / len(passes)
    else:
        return None
    
    return profile

def validate_cluster_separation(df, position, role_templates):
    """
    클러스터 간 구분력 검증
    
    각 롤 간 주요 지표의 차이가 통계적으로 유의한지 확인
    """
    if position not in role_templates:
        return None
    
    print(f"\n{'='*80}")
    print(f"{position} 포지션 롤 구분력 검증")
    print(f"{'='*80}")
    
    position_players = df[df['main_position'] == position]
    player_ids = position_players['player_id'].dropna().unique()
    
    # 각 선수의 프로파일 계산
    player_profiles = {}
    for player_id in player_ids:
        profile = calculate_player_profile(df, player_id)
        if profile:
            player_profiles[player_id] = profile
    
    # 각 롤에 속한 선수들 찾기 (템플릿과의 유사도로)
    from scipy.spatial.distance import cosine
    
    role_assignments = {}
    for role_name, template in role_templates[position].items():
        role_assignments[role_name] = []
        
        for player_id, profile in player_profiles.items():
            # 간단한 유사도 계산 (주요 지표만)
            player_vector = [profile.get('long_pass_ratio', 0), 
                           profile.get('average_touch_y', 0) / 100,  # 정규화
                           profile.get('pass_success_rate', 0)]
            template_vector = [template.get('long_pass_ratio', 0),
                            template.get('average_touch_y', 0) / 100,
                            template.get('pass_success_rate', 0)]
            
            try:
                similarity = 1 - cosine(player_vector, template_vector)
                role_assignments[role_name].append((player_id, similarity))
            except:
                pass
        
        # 가장 유사한 롤에 할당
        role_assignments[role_name].sort(key=lambda x: x[1], reverse=True)
    
    # 각 롤별 주요 지표 분포 확인
    print(f"\n[롤별 주요 지표 분포]")
    key_metrics = ['long_pass_ratio', 'average_touch_y', 'pass_success_rate']
    
    for metric in key_metrics:
        print(f"\n{metric}:")
        role_values = {}
        
        for role_name in role_assignments.keys():
            values = []
            for player_id, _ in role_assignments[role_name][:20]:  # 상위 20명만
                if player_id in player_profiles:
                    value = player_profiles[player_id].get(metric, 0)
                    if metric == 'average_touch_y':
                        values.append(value)
                    else:
                        values.append(value)
            
            if len(values) > 0:
                role_values[role_name] = values
                avg = np.mean(values)
                std = np.std(values)
                print(f"  {role_name}: 평균 {avg:.3f}, 표준편차 {std:.3f}, 범위 [{np.min(values):.3f}, {np.max(values):.3f}]")
        
        # ANOVA 검정 (롤 간 차이가 유의한지)
        if len(role_values) >= 2:
            groups = [role_values[r] for r in role_values.keys() if len(role_values[r]) > 0]
            if len(groups) >= 2:
                try:
                    f_stat, p_value = f_oneway(*groups)
                    significance = "유의함" if p_value < 0.05 else "유의하지 않음"
                    print(f"  → ANOVA 검정: p-value={p_value:.4f} ({significance})")
                except:
                    print(f"  → ANOVA 검정: 계산 불가")
    
    return role_assignments

def main():
    print("="*80)
    print("롤 클러스터링 결과 검증")
    print("="*80)
    print("\n목적: 클러스터링으로 생성된 롤들이 실제로 의미 있는 구분인지 확인")
    print("방법: 각 롤 간 주요 지표의 통계적 차이 검증 (ANOVA)\n")
    
    df = load_data()
    role_templates = load_role_templates()
    
    if role_templates is None:
        print("❌ 롤 템플릿 파일을 찾을 수 없습니다.")
        print("   먼저 analysis/define_roles_from_data.py를 실행하세요.")
        return
    
    # 주요 포지션 검증
    main_positions = ['CM', 'CB', 'CF']
    
    for position in main_positions:
        if position in role_templates:
            validate_cluster_separation(df, position, role_templates)
    
    print("\n" + "="*80)
    print("검증 완료")
    print("="*80)
    print("\n주의: 이 검증은 클러스터 간 통계적 차이만 확인합니다.")
    print("      실제 축구 도메인에서의 롤 의미는 전문가 검토가 필요합니다.")

if __name__ == '__main__':
    main()


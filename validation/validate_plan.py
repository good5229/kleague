"""
기획안 검증 스크립트

목적: PLAN.md에 제시된 3번(선수 강점-롤 적합도 분석기)과 4번(전술 완성도 + 엔터테인먼트 통합 스코어)의
      핵심 지표들이 실제 데이터로 계산 가능한지 검증

주의: 이 스크립트는 "계산 가능 여부"만 확인합니다. 실제 성능/결과 해석은 별도 검토가 필요합니다.
"""

import pandas as pd
import numpy as np
from pathlib import Path

# 프로젝트 루트 경로
PROJECT_ROOT = Path(__file__).parent.parent

def load_data():
    """데이터 로딩"""
    print("=" * 60)
    print("1. 데이터 로딩")
    print("=" * 60)
    
    df = pd.read_csv(PROJECT_ROOT / 'raw_data' / 'open_track2' / 'raw_data.csv')
    match_info_df = pd.read_csv(PROJECT_ROOT / 'raw_data' / 'open_track2' / 'match_info.csv')
    
    print(f"✓ raw_data.csv 로딩 완료: {len(df):,} 행")
    print(f"✓ match_info.csv 로딩 완료: {len(match_info_df):,} 행")
    print(f"✓ 경기 수: {df['game_id'].nunique():,} 경기")
    print(f"✓ 선수 수: {df['player_id'].dropna().nunique():,} 명")
    print(f"✓ 팀 수: {df['team_id'].nunique():,} 팀")
    
    return df, match_info_df

def validate_data_columns(df, match_info_df):
    """필요한 컬럼이 모두 존재하는지 검증"""
    print("\n" + "=" * 60)
    print("2. 데이터 컬럼 검증")
    print("=" * 60)
    
    # 3번 기획안에 필요한 컬럼
    required_cols_plan3 = [
        'game_id', 'player_id', 'player_name_ko', 'team_id', 'team_name_ko',
        'position_name', 'main_position', 'type_name', 'result_name',
        'start_x', 'start_y', 'end_x', 'end_y', 'dx', 'dy', 'time_seconds'
    ]
    
    # 4번 기획안에 필요한 컬럼
    required_cols_plan4 = [
        'game_id', 'team_id', 'type_name', 'result_name',
        'start_x', 'start_y', 'end_x', 'end_y', 'dx', 'dy',
        'time_seconds', 'period_id'
    ]
    
    required_cols_match = ['game_id', 'home_team_id', 'away_team_id', 'home_score', 'away_score']
    
    missing_cols_df = [col for col in required_cols_plan3 + required_cols_plan4 if col not in df.columns]
    missing_cols_match = [col for col in required_cols_match if col not in match_info_df.columns]
    
    if missing_cols_df:
        print(f"❌ raw_data.csv에 누락된 컬럼: {missing_cols_df}")
        return False
    elif missing_cols_match:
        print(f"❌ match_info.csv에 누락된 컬럼: {missing_cols_match}")
        return False
    else:
        print("✓ 모든 필수 컬럼이 존재합니다.")
        return True

def validate_plan3_metrics(df):
    """3번 기획안: 선수 강점-롤 적합도 분석기 지표 계산 가능 여부 검증"""
    print("\n" + "=" * 60)
    print("3. 기획안 3번 검증: 선수 강점-롤 적합도 분석기")
    print("=" * 60)
    
    # 샘플 선수 1명 선택 (데이터가 충분한 선수)
    player_counts = df['player_id'].value_counts()
    sample_player_id = player_counts[player_counts >= 100].index[0]  # 최소 100개 이벤트 이상
    
    player_data = df[df['player_id'] == sample_player_id].copy()
    print(f"\n검증 대상 선수: player_id={sample_player_id}, 이벤트 수={len(player_data)}")
    
    validation_results = {}
    
    # 1. 전진 패스 비율 계산
    try:
        passes = player_data[player_data['type_name'] == 'Pass']
        if len(passes) > 0:
            forward_passes = passes[passes['dx'] > 0]
            forward_pass_ratio = len(forward_passes) / len(passes)
            validation_results['forward_pass_ratio'] = True
            print(f"✓ 전진 패스 비율 계산 가능: {forward_pass_ratio:.2%}")
        else:
            validation_results['forward_pass_ratio'] = False
            print("⚠ 전진 패스 비율: 패스 데이터 부족")
    except Exception as e:
        validation_results['forward_pass_ratio'] = False
        print(f"❌ 전진 패스 비율 계산 실패: {e}")
    
    # 2. 롱패스 비율 계산
    try:
        if len(passes) > 0:
            pass_lengths = np.sqrt(passes['dx']**2 + passes['dy']**2)
            long_passes = (pass_lengths > 20).sum()
            long_pass_ratio = long_passes / len(passes)
            validation_results['long_pass_ratio'] = True
            print(f"✓ 롱패스 비율 계산 가능: {long_pass_ratio:.2%}")
        else:
            validation_results['long_pass_ratio'] = False
    except Exception as e:
        validation_results['long_pass_ratio'] = False
        print(f"❌ 롱패스 비율 계산 실패: {e}")
    
    # 3. 패스 성공률 계산
    try:
        if len(passes) > 0:
            successful_passes = passes[passes['result_name'] == 'Successful']
            pass_success_rate = len(successful_passes) / len(passes)
            validation_results['pass_success_rate'] = True
            print(f"✓ 패스 성공률 계산 가능: {pass_success_rate:.2%}")
        else:
            validation_results['pass_success_rate'] = False
    except Exception as e:
        validation_results['pass_success_rate'] = False
        print(f"❌ 패스 성공률 계산 실패: {e}")
    
    # 4. 평균 터치 위치 계산
    try:
        avg_touch_x = player_data['start_x'].mean()
        avg_touch_y = player_data['start_y'].mean()
        validation_results['average_touch_position'] = True
        print(f"✓ 평균 터치 위치 계산 가능: ({avg_touch_x:.1f}, {avg_touch_y:.1f})")
    except Exception as e:
        validation_results['average_touch_position'] = False
        print(f"❌ 평균 터치 위치 계산 실패: {e}")
    
    # 5. 공간 활용 지표 (중앙/측면/전진 지역)
    try:
        central_touches = player_data[(player_data['start_x'] >= 30) & (player_data['start_x'] <= 70)]
        central_ratio = len(central_touches) / len(player_data)
        validation_results['spatial_usage'] = True
        print(f"✓ 공간 활용 지표 계산 가능: 중앙 지역 터치 비율 {central_ratio:.2%}")
    except Exception as e:
        validation_results['spatial_usage'] = False
        print(f"❌ 공간 활용 지표 계산 실패: {e}")
    
    # 6. 수비 행동 빈도
    try:
        interventions = player_data[player_data['type_name'] == 'Intervention']
        blocks = player_data[player_data['type_name'] == 'Block']
        defensive_frequency = (len(interventions) + len(blocks)) / len(player_data)
        validation_results['defensive_actions'] = True
        print(f"✓ 수비 행동 빈도 계산 가능: {defensive_frequency:.2%}")
    except Exception as e:
        validation_results['defensive_actions'] = False
        print(f"❌ 수비 행동 빈도 계산 실패: {e}")
    
    # 종합 결과
    success_count = sum(validation_results.values())
    total_count = len(validation_results)
    print(f"\n[3번 기획안 검증 결과] {success_count}/{total_count} 지표 계산 가능")
    
    return validation_results

def validate_plan4_metrics(df, match_info_df):
    """4번 기획안: 전술 완성도 + 엔터테인먼트 통합 스코어 지표 계산 가능 여부 검증"""
    print("\n" + "=" * 60)
    print("4. 기획안 4번 검증: 전술 완성도 + 엔터테인먼트 통합 스코어")
    print("=" * 60)
    
    # 샘플 경기 1개 선택
    sample_game_id = df['game_id'].iloc[0]
    game_data = df[df['game_id'] == sample_game_id].copy()
    game_match_info = match_info_df[match_info_df['game_id'] == sample_game_id].iloc[0]
    
    print(f"\n검증 대상 경기: game_id={sample_game_id}")
    print(f"홈팀: {game_match_info.get('home_team_name_ko', 'N/A')}, "
          f"원정팀: {game_match_info.get('away_team_name_ko', 'N/A')}")
    print(f"스코어: {game_match_info['home_score']}-{game_match_info['away_score']}")
    
    validation_results = {}
    
    # === 전술 완성도 지수 관련 ===
    
    # 1. 공간 점유 균형 지수
    try:
        # 필드를 9개 구역으로 분할 (간단한 예시: 3x3)
        home_team_id = game_match_info['home_team_id']
        away_team_id = game_match_info['away_team_id']
        
        home_events = game_data[game_data['team_id'] == home_team_id]
        away_events = game_data[game_data['team_id'] == away_team_id]
        
        # 중앙 지역(30 < x < 70, 30 < y < 70) 점유 시간 계산
        home_central = home_events[(home_events['start_x'] >= 30) & (home_events['start_x'] < 70) &
                                   (home_events['start_y'] >= 30) & (home_events['start_y'] < 70)]
        away_central = away_events[(away_events['start_x'] >= 30) & (away_events['start_x'] < 70) &
                                   (away_events['start_y'] >= 30) & (away_events['start_y'] < 70)]
        
        home_possession = len(home_central)
        away_possession = len(away_central)
        total_possession = home_possession + away_possession
        
        if total_possession > 0:
            balance_score = 1 - abs(home_possession - away_possession) / total_possession
            validation_results['spatial_control_balance'] = True
            print(f"✓ 공간 점유 균형 지수 계산 가능: {balance_score:.3f}")
        else:
            validation_results['spatial_control_balance'] = False
            print("⚠ 공간 점유 균형 지수: 데이터 부족")
    except Exception as e:
        validation_results['spatial_control_balance'] = False
        print(f"❌ 공간 점유 균형 지수 계산 실패: {e}")
    
    # 2. 전진 효율 지수
    try:
        home_passes = home_events[home_events['type_name'] == 'Pass']
        if len(home_passes) > 0:
            forward_passes = home_passes[home_passes['dx'] > 0]
            forward_ratio = len(forward_passes) / len(home_passes)
            forward_success = forward_passes[forward_passes['result_name'] == 'Successful']
            forward_success_rate = len(forward_success) / len(forward_passes) if len(forward_passes) > 0 else 0
            validation_results['progression_efficiency'] = True
            print(f"✓ 전진 효율 지수 계산 가능: 전진 패스 비율 {forward_ratio:.2%}, 성공률 {forward_success_rate:.2%}")
        else:
            validation_results['progression_efficiency'] = False
            print("⚠ 전진 효율 지수: 패스 데이터 부족")
    except Exception as e:
        validation_results['progression_efficiency'] = False
        print(f"❌ 전진 효율 지수 계산 실패: {e}")
    
    # 3. 빌드업 다양성 (간단 버전: 참여 선수 수)
    try:
        home_players = home_events['player_id'].dropna().nunique()
        away_players = away_events['player_id'].dropna().nunique()
        validation_results['build_up_diversity'] = True
        print(f"✓ 빌드업 다양성 지표 계산 가능: 홈팀 참여 선수 {home_players}명, 원정팀 {away_players}명")
    except Exception as e:
        validation_results['build_up_diversity'] = False
        print(f"❌ 빌드업 다양성 지표 계산 실패: {e}")
    
    # === 엔터테인먼트 지수 관련 ===
    
    # 4. 공격 강도 지수
    try:
        shots = game_data[game_data['type_name'] == 'Shot']
        danger_zone = game_data[(game_data['start_y'] > 80) & (game_data['start_x'] >= 20) & (game_data['start_x'] <= 80)]
        shot_frequency = len(shots)
        danger_entries = len(danger_zone)
        validation_results['attacking_intensity'] = True
        print(f"✓ 공격 강도 지수 계산 가능: 슈팅 {shot_frequency}회, 위험 지역 진입 {danger_entries}회")
    except Exception as e:
        validation_results['attacking_intensity'] = False
        print(f"❌ 공격 강도 지수 계산 실패: {e}")
    
    # 5. 볼 소유 전환 빈도
    try:
        # team_id가 연속으로 바뀌는 횟수 계산
        team_changes = (game_data['team_id'].shift() != game_data['team_id']).sum()
        game_duration_min = game_data['time_seconds'].max() / 60  # 경기 시간(분)
        turnover_frequency = team_changes / game_duration_min if game_duration_min > 0 else 0
        validation_results['possession_turnover'] = True
        print(f"✓ 볼 소유 전환 빈도 계산 가능: {turnover_frequency:.2f} 회/분")
    except Exception as e:
        validation_results['possession_turnover'] = False
        print(f"❌ 볼 소유 전환 빈도 계산 실패: {e}")
    
    # 6. 스코어 변동 지수
    try:
        home_score = game_match_info['home_score']
        away_score = game_match_info['away_score']
        total_goals = home_score + away_score
        comeback = 1 if (home_score > 0 and away_score > 0) else 0  # 간단 버전
        validation_results['score_dynamics'] = True
        print(f"✓ 스코어 변동 지수 계산 가능: 총 득점 {total_goals}골")
    except Exception as e:
        validation_results['score_dynamics'] = False
        print(f"❌ 스코어 변동 지수 계산 실패: {e}")
    
    # 종합 결과
    success_count = sum(validation_results.values())
    total_count = len(validation_results)
    print(f"\n[4번 기획안 검증 결과] {success_count}/{total_count} 지표 계산 가능")
    
    return validation_results

def check_data_quality(df, match_info_df):
    """데이터 품질 체크 (결측치, 이상치 등)"""
    print("\n" + "=" * 60)
    print("5. 데이터 품질 체크")
    print("=" * 60)
    
    # 결측치 체크
    print("\n[결측치 비율]")
    missing_ratios = df.isnull().sum() / len(df) * 100
    important_cols = ['player_id', 'type_name', 'result_name', 'start_x', 'start_y', 'dx', 'dy']
    for col in important_cols:
        if col in missing_ratios.index:
            ratio = missing_ratios[col]
            status = "⚠" if ratio > 10 else "✓"
            print(f"{status} {col}: {ratio:.1f}%")
    
    # 좌표 범위 체크
    print("\n[좌표 범위]")
    print(f"start_x: {df['start_x'].min():.1f} ~ {df['start_x'].max():.1f}")
    print(f"start_y: {df['start_y'].min():.1f} ~ {df['start_y'].max():.1f}")
    print(f"end_x: {df['end_x'].min():.1f} ~ {df['end_x'].max():.1f}")
    print(f"end_y: {df['end_y'].min():.1f} ~ {df['end_y'].max():.1f}")
    
    # 이벤트 타입 분포
    print("\n[이벤트 타입 분포]")
    event_counts = df['type_name'].value_counts().head(10)
    for event_type, count in event_counts.items():
        print(f"  {event_type}: {count:,} ({count/len(df)*100:.1f}%)")

def main():
    """메인 실행 함수"""
    print("\n" + "=" * 60)
    print("기획안 검증 스크립트 실행")
    print("=" * 60)
    print("\n주의: 이 스크립트는 '계산 가능 여부'만 확인합니다.")
    print("실제 성능/결과 해석은 별도 검토가 필요합니다.\n")
    
    # 데이터 로딩
    df, match_info_df = load_data()
    
    # 컬럼 검증
    if not validate_data_columns(df, match_info_df):
        print("\n❌ 필수 컬럼이 누락되어 검증을 중단합니다.")
        return
    
    # 데이터 품질 체크
    check_data_quality(df, match_info_df)
    
    # 기획안별 검증
    plan3_results = validate_plan3_metrics(df)
    plan4_results = validate_plan4_metrics(df, match_info_df)
    
    # 최종 요약
    print("\n" + "=" * 60)
    print("최종 검증 요약")
    print("=" * 60)
    print(f"\n[3번 기획안] {sum(plan3_results.values())}/{len(plan3_results)} 지표 계산 가능")
    print(f"[4번 기획안] {sum(plan4_results.values())}/{len(plan4_results)} 지표 계산 가능")
    
    if all(plan3_results.values()) and all(plan4_results.values()):
        print("\n✓ 모든 핵심 지표가 계산 가능합니다. 기획안 구현을 진행할 수 있습니다.")
    else:
        print("\n⚠ 일부 지표 계산에 문제가 있을 수 있습니다. 데이터 전처리 또는 지표 정의 수정이 필요할 수 있습니다.")

if __name__ == '__main__':
    main()


"""
랭킹 검증 스크립트

특정 선수(아론, 정태욱 등)의 랭킹이 실제 성과와 일치하는지 검증
"""

import pandas as pd
import json
from pathlib import Path
from collections import defaultdict

PROJECT_ROOT = Path(__file__).parent.parent

def load_data():
    """데이터 로딩"""
    df = pd.read_csv(PROJECT_ROOT / 'raw_data' / 'open_track2' / 'raw_data.csv')
    match_info_df = pd.read_csv(PROJECT_ROOT / 'raw_data' / 'open_track2' / 'match_info.csv')
    return df, match_info_df

def calculate_team_win_rate(df, match_info_df, player_id):
    """선수의 팀 승률 계산"""
    player_data = df[df['player_id'] == player_id]
    if len(player_data) == 0:
        return None
    
    player_games = player_data['game_id'].unique()
    wins = 0
    draws = 0
    losses = 0
    
    for game_id in player_games:
        game_info = match_info_df[match_info_df['game_id'] == game_id]
        if len(game_info) > 0:
            game_data = player_data[player_data['game_id'] == game_id]
            if len(game_data) > 0:
                player_team_id = game_data['team_id'].iloc[0]
                is_home = game_info['home_team_id'].iloc[0] == player_team_id
                home_score = game_info['home_score'].iloc[0]
                away_score = game_info['away_score'].iloc[0]
                
                if is_home:
                    if home_score > away_score:
                        wins += 1
                    elif home_score == away_score:
                        draws += 1
                    else:
                        losses += 1
                else:
                    if away_score > home_score:
                        wins += 1
                    elif away_score == home_score:
                        draws += 1
                    else:
                        losses += 1
    
    game_count = len(player_games)
    win_rate = wins / game_count if game_count > 0 else 0
    
    return {
        'game_count': game_count,
        'wins': wins,
        'draws': draws,
        'losses': losses,
        'win_rate': win_rate
    }

def validate_specific_players():
    """특정 선수들의 랭킹 검증"""
    df, match_info_df = load_data()
    
    players_to_check = ['아론', '정태욱']
    
    print("="*80)
    print("특정 선수 랭킹 검증")
    print("="*80)
    print()
    
    for player_name in players_to_check:
        player_data = df[df['player_name_ko'] == player_name]
        if len(player_data) == 0:
            print(f"{player_name}을 찾을 수 없습니다.")
            continue
        
        player_id = player_data['player_id'].iloc[0]
        team = player_data['team_name_ko'].iloc[0]
        position = player_data['main_position'].iloc[0]
        game_count = player_data['game_id'].nunique()
        
        # 팀 승률 계산
        win_rate_info = calculate_team_win_rate(df, match_info_df, player_id)
        
        print(f"{player_name} ({position}, {team}):")
        print(f"  경기 수: {game_count}경기")
        if win_rate_info:
            print(f"  팀 승률: {win_rate_info['wins']}승 {win_rate_info['draws']}무 {win_rate_info['losses']}패 ({win_rate_info['win_rate']:.1%})")
        
        # 경기 수 보너스 계산
        game_bonus = 0.0
        if game_count >= 30:
            game_bonus = 3.0
        elif game_count >= 25:
            game_bonus = 2.0
        elif game_count >= 20:
            game_bonus = 1.0
        elif game_count >= 15:
            game_bonus = 0.5
        
        # 팀 승률 보너스/페널티 계산
        if win_rate_info:
            win_rate = win_rate_info['win_rate']
            win_rate_bonus = 0.0
            if win_rate >= 0.6:
                win_rate_bonus = 1.0
            elif win_rate >= 0.5:
                win_rate_bonus = 0.5
            elif win_rate < 0.3:
                win_rate_bonus = -1.0
            elif win_rate < 0.4:
                win_rate_bonus = -0.5
            
            print(f"  경기 수 보너스: +{game_bonus:.1f}점")
            print(f"  팀 승률 기여도: {win_rate_bonus:+.1f}점")
            print(f"  총 보너스: {game_bonus + win_rate_bonus:+.1f}점")
        
        print()
    
    print("="*80)
    print("검증 완료")
    print("="*80)
    print()
    print("참고:")
    print("- 경기 수 보너스: 한 시즌 꾸준히 뛴 선수에게 가치 부여")
    print("- 팀 승률 기여도: 해당 선수가 뛴 경기에서 팀 승률이 낮으면 페널티")
    print("- 낮은 승률(30% 미만)은 -1.0점 페널티, 40% 미만은 -0.5점 페널티")

if __name__ == '__main__':
    validate_specific_players()


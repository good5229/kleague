https://dacon.io/competitions/official/236648/overview/description# kleague

## kleague

### 데이터셋 구성

- **`raw_data/open_track2/match_info.csv`**  
  - K리그 1 경기 단위 정보가 정리된 테이블  
  - 주요 컬럼:  
    - `game_id`: 경기 고유 ID  
    - `season_id`, `season_name`: 시즌 정보  
    - `competition_id`, `competition_name`, `country_name`: 대회/리그 정보  
    - `game_day`, `game_date`: 라운드/킥오프 일시  
    - `home_team_id`, `away_team_id`: 홈/원정 팀 ID  
    - `home_team_name`, `home_team_name_ko`, `away_team_name`, `away_team_name_ko`: 팀 영문/한글명  
    - `home_score`, `away_score`: 최종 득점 (경기 결과)

- **`raw_data/open_track2/raw_data.csv`**  
  - 각 경기에서 발생한 이벤트(패스, 캐리, 슈팅, 인터벤션 등)를 개별 레코드로 담은 이벤트 로그  
  - 주요 컬럼:  
    - `game_id`: 어느 경기에서 발생한 이벤트인지 식별  
    - `action_id`: 경기 내 이벤트 순번  
    - `period_id`: 전반/후반 등 피리어드 구분  
    - `time_seconds`: 해당 피리어드 내 발생 시각(초 단위)  
    - `team_id`, `team_name_ko`: 이벤트를 수행한 팀 정보  
    - `player_id`, `player_name_ko`: 이벤트를 수행한 선수 정보  
    - `position_name`, `main_position`: 포지션 정보  
    - `type_name`: 이벤트 종류 (예: Pass, Pass Received, Carry, Shot, Block, Out, Intervention, Recovery 등)  
    - `result_name`: 이벤트 결과 (Successful, Unsuccessful 등)  
    - `start_x`, `start_y`, `end_x`, `end_y`, `dx`, `dy`: 피치 상 좌표 및 이동 벡터

- **`raw_data/open_track2/data_description.xlsx`**  
  - 위 `match_info.csv` 및 `raw_data.csv`에 포함된 각 컬럼의 정의, 데이터 타입, 값의 범위 등을 정리한 데이터 사전  
  - 분석 시 `desc_df`로 로딩하여 컬럼별 의미를 참고하는 용도로 사용

이 프로젝트에서는 `desc_df`(컬럼 설명), `match_info_df`(경기 단위 정보), `df`(이벤트 단위 로그)를 함께 활용하여 K리그 경기/선수/전술 패턴을 분석하고, 데이터 기반 AI 서비스를 탐색한다.



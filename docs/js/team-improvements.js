// 팀 개선점 분석 및 베스트 11 관련 함수

let teamImprovementsData = null;
let best11Data = null;

// 개선점 데이터 로딩
async function loadTeamImprovements() {
    try {
        const response = await fetch('data/team_improvements.json');
        if (!response.ok) {
            throw new Error('개선점 데이터를 불러올 수 없습니다.');
        }
        const data = await response.json();
        teamImprovementsData = data.team_improvements;
        best11Data = data.best_11;
        return data;
    } catch (error) {
        console.error('Error loading team improvements:', error);
        return null;
    }
}

// 팀 개선점 렌더링
function renderTeamImprovements(teamName) {
    if (!teamImprovementsData || !teamImprovementsData[teamName]) {
        return '<p>개선점 데이터가 없습니다.</p>';
    }
    
    const improvements = teamImprovementsData[teamName];
    const weaknesses = improvements.weaknesses;
    const recommendations = improvements.recommendations;
    
    let html = '<div class="team-improvements-container">';
    
    // 약점 요약
    html += '<div class="weaknesses-summary">';
    html += '<h3>팀 약점 분석</h3>';
    
    if (weaknesses.quality_gaps && weaknesses.quality_gaps.length > 0) {
        html += '<div class="quality-gaps">';
        html += '<h4>품질 격차</h4>';
        html += '<ul>';
        weaknesses.quality_gaps.forEach(gap => {
            html += `<li>${gap.reason}</li>`;
        });
        html += '</ul>';
        html += '</div>';
    }
    
    html += '</div>';
    
    // 추천 선수
    if (recommendations && recommendations.length > 0) {
        html += '<div class="recommendations-section">';
        html += '<h3>추천 선수</h3>';
        
        recommendations.forEach(rec => {
            html += '<div class="recommendation-group">';
            
            if (rec.gap_type === 'position') {
                html += `<h4>${rec.position} 포지션 보완</h4>`;
                html += `<p class="gap-info">현재 평균 점수: ${rec.current_average}점</p>`;
            } else if (rec.gap_type === 'role') {
                html += `<h4>${rec.role} 역할 보완</h4>`;
                if (rec.current_count !== undefined) {
                    html += `<p class="gap-info">현재 보유 선수: ${rec.current_count}명</p>`;
                } else if (rec.current_max_score !== undefined) {
                    html += `<p class="gap-info">현재 최고 점수: ${rec.current_max_score}점</p>`;
                }
            }
            
            html += '<div class="recommended-players-list">';
            rec.recommended_players.forEach(player => {
                const teamColor = getTeamColor(player.team_name);
                html += `
                    <div class="recommended-player-card" 
                         onclick="selectPlayer(${player.player_id})"
                         style="border-left: 4px solid ${teamColor.primary}">
                        <div class="player-header">
                            <h5>${player.player_name}</h5>
                            <span class="player-team">${player.team_name}</span>
                        </div>
                        <div class="player-info">
                            <span class="position">${player.position}</span>
                            <span class="role">${player.role}</span>
                            <span class="fit-score">${player.fit_score}점</span>
                        </div>
                        <div class="improvement-info">
                            <span class="improvement-badge">+${player.improvement_potential}점 향상</span>
                            <span class="game-count">${player.game_count}경기</span>
                        </div>
                        <p class="recommendation-reason">${player.reason}</p>
                    </div>
                `;
            });
            html += '</div>';
            html += '</div>';
        });
        
        html += '</div>';
    } else {
        html += '<p>현재 추천할 선수가 없습니다. 팀의 전반적인 수준이 우수합니다.</p>';
    }
    
    html += '</div>';
    return html;
}

// 포메이션별 배치 순서 정의
const FORMATION_LAYOUTS = {
    '4-4-2': [
        ['GK'],
        ['LB', 'CB', 'CB', 'RB'],
        ['LM', 'CM', 'CM', 'RM'],
        ['ST', 'ST']
    ],
    '4-3-3': [
        ['GK'],
        ['LB', 'CB', 'CB', 'RB'],
        ['CDM', 'CM', 'CM'],
        ['LW', 'ST', 'RW']
    ],
    '5-3-2': [
        ['GK'],
        ['LWB', 'CB', 'CB', 'CB', 'RWB'],
        ['CM', 'CM', 'CM'],
        ['ST', 'ST']
    ],
    '4-3-1-2': [
        ['GK'],
        ['LB', 'CB', 'CB', 'RB'],
        ['CM', 'CM', 'CM'],
        ['CAM'],
        ['ST', 'ST']
    ],
    '4-5-1': [
        ['GK'],
        ['LB', 'CB', 'CB', 'RB'],
        ['LM', 'CM', 'CM', 'CM', 'RM'],
        ['ST']
    ]
};

// 포메이션별 포지션 매핑 (LM/RM -> CM, LWB/RWB -> LB/RB 등)
const POSITION_MAPPING = {
    'LM': 'CM',
    'RM': 'CM',
    'LWB': 'LB',
    'RWB': 'RB'
};

// 베스트 11 렌더링
function renderBest11(selectedFormation = '4-3-3') {
    if (!best11Data || !best11Data[selectedFormation]) {
        return '<p>베스트 11 데이터가 없습니다.</p>';
    }
    
    const formationData = best11Data[selectedFormation];
    const formation = FORMATION_LAYOUTS[selectedFormation] || FORMATION_LAYOUTS['4-3-3'];
    
    let html = '<div class="best-11-container">';
    
    // 포메이션 선택 셀렉트박스
    html += '<div class="formation-selector">';
    html += '<label for="formation-select">포메이션 선택: </label>';
    html += '<select id="formation-select" onchange="changeFormation(this.value)">';
    Object.keys(FORMATION_LAYOUTS).forEach(formationName => {
        html += `<option value="${formationName}" ${formationName === selectedFormation ? 'selected' : ''}>${formationName}</option>`;
    });
    html += '</select>';
    html += '</div>';
    
    html += '<div class="formation-diagram">';
    
    // 전체 선수 중복 방지를 위한 집합
    const usedPlayerIds = new Set();
    
    formation.forEach((row, rowIdx) => {
        html += '<div class="formation-row">';
        row.forEach((position, posIdx) => {
            // 포지션 매핑 적용 (LM -> CM, LWB -> LB 등)
            const mappedPosition = POSITION_MAPPING[position] || position;
            let players = formationData[mappedPosition] || [];
            
            // 정확한 포지션도 확인
            if (formationData[position] && formationData[position].length > 0) {
                players = formationData[position];
            }
            
            // 해당 포지션의 선수 찾기 (중복 방지)
            let player = null;
            
            if (players.length > 0) {
                // 사용되지 않은 선수 찾기
                for (const p of players) {
                    if (!usedPlayerIds.has(p.player_id)) {
                        player = p;
                        usedPlayerIds.add(p.player_id);
                        break;
                    }
                }
            }
            
            if (player) {
                const teamColor = getTeamColor(player.team_name);
                // 팀 이름 색상 적용 (가독성을 위해 배경색과 대비되는 색상 사용)
                const textColor = getContrastColor(teamColor.primary);
                html += `
                    <div class="best-11-player" 
                         onclick="selectPlayer(${player.player_id})"
                         style="border: 2px solid ${teamColor.primary}">
                        <div class="player-name">${player.player_name}</div>
                        <div class="player-position">${position}</div>
                        <div class="player-role">${player.role}</div>
                        <div class="player-score">${player.fit_score}점</div>
                        <div class="player-team" style="background: ${teamColor.primary}; color: ${textColor}; padding: 4px 8px; border-radius: 4px; font-size: 0.85em; font-weight: bold;">${player.team_name}</div>
                    </div>
                `;
            } else {
                html += `<div class="best-11-player empty">${position}</div>`;
            }
        });
        html += '</div>';
    });
    
    html += '</div>';
    
    // 상세 정보
    html += '<div class="best-11-details">';
    html += '<h3>포지션별 최고 선수</h3>';
    
    // 선택된 포메이션의 포지션 순서
    const positionOrder = Object.keys(formationData).sort();
    positionOrder.forEach(position => {
        const players = formationData[position] || [];
        if (players.length > 0) {
            html += `<div class="position-group">`;
            html += `<h4>${position}</h4>`;
            html += '<div class="position-players">';
            players.forEach(player => {
                const teamColor = getTeamColor(player.team_name);
                const textColor = getContrastColor(teamColor.primary);
                html += `
                    <div class="best-11-detail-card"
                         onclick="selectPlayer(${player.player_id})"
                         style="border-left: 4px solid ${teamColor.primary}">
                        <div class="detail-header">
                            <span class="detail-name">${player.player_name}</span>
                            <span class="detail-team" style="background: ${teamColor.primary}; color: ${textColor}; padding: 4px 8px; border-radius: 4px; font-size: 0.85em; font-weight: bold;">${player.team_name}</span>
                        </div>
                        <div class="detail-info">
                            <span class="detail-role">${player.role}</span>
                            <span class="detail-score">${player.fit_score}점</span>
                            <span class="detail-games">${player.game_count}경기</span>
                        </div>
                    </div>
                `;
            });
            html += '</div>';
            html += '</div>';
        }
    });
    
    html += '</div>';
    html += '</div>';
    
    return html;
}

// 베스트 11 페이지 표시
function showBest11() {
    if (!best11Data) {
        loadTeamImprovements().then(() => {
            if (best11Data) {
                displayBest11();
            }
        });
    } else {
        displayBest11();
    }
}

function displayBest11() {
    // 섹션 전환
    document.getElementById('team-selection').classList.add('hidden');
    document.getElementById('player-list').classList.add('hidden');
    document.getElementById('player-detail').classList.add('hidden');
    document.getElementById('team-analysis').classList.add('hidden');
    document.getElementById('best-11').classList.remove('hidden');
    
    // 베스트 11 렌더링 (기본 포메이션: 4-3-3)
    const content = document.getElementById('best-11-content');
    content.innerHTML = renderBest11('4-3-3');
}

// 대비 색상 계산 (가독성을 위해)
function getContrastColor(hexColor) {
    // HEX를 RGB로 변환
    const r = parseInt(hexColor.slice(1, 3), 16);
    const g = parseInt(hexColor.slice(3, 5), 16);
    const b = parseInt(hexColor.slice(5, 7), 16);
    
    // 상대 휘도 계산
    const luminance = (0.299 * r + 0.587 * g + 0.114 * b) / 255;
    
    // 밝으면 검은색, 어두우면 흰색 반환
    return luminance > 0.5 ? '#000000' : '#ffffff';
}

// 포메이션 변경
function changeFormation(formationName) {
    const content = document.getElementById('best-11-content');
    content.innerHTML = renderBest11(formationName);
}

// 전역 함수로 노출
window.renderTeamImprovements = renderTeamImprovements;
window.showBest11 = showBest11;
window.loadTeamImprovements = loadTeamImprovements;
window.changeFormation = changeFormation;


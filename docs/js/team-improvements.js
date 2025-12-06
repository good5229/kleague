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

// 베스트 11 렌더링
function renderBest11() {
    if (!best11Data) {
        return '<p>베스트 11 데이터가 없습니다.</p>';
    }
    
    // 포지션별 배치 순서 (포메이션 4-3-3 기준)
    const formation = [
        ['GK'],
        ['LB', 'CB', 'CB', 'RB'],
        ['CDM', 'CM', 'CM'],
        ['CAM'],
        ['LW', 'ST', 'RW']
    ];
    
    let html = '<div class="best-11-container">';
    html += '<div class="formation-diagram">';
    
    formation.forEach((row, rowIdx) => {
        html += '<div class="formation-row">';
        row.forEach(position => {
            const players = best11Data[position] || [];
            if (players.length > 0) {
                const player = players[0]; // 첫 번째 선수 선택
                const teamColor = getTeamColor(player.team_name);
                html += `
                    <div class="best-11-player" 
                         onclick="selectPlayer(${player.player_id})"
                         style="border: 2px solid ${teamColor.primary}">
                        <div class="player-name">${player.player_name}</div>
                        <div class="player-position">${position}</div>
                        <div class="player-role">${player.role}</div>
                        <div class="player-score">${player.fit_score}점</div>
                        <div class="player-team">${player.team_name}</div>
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
    
    const positionOrder = ['GK', 'CB', 'LB', 'RB', 'CDM', 'CM', 'CAM', 'LW', 'RW', 'ST', 'CF'];
    positionOrder.forEach(position => {
        const players = best11Data[position] || [];
        if (players.length > 0) {
            html += `<div class="position-group">`;
            html += `<h4>${position}</h4>`;
            html += '<div class="position-players">';
            players.forEach(player => {
                const teamColor = getTeamColor(player.team_name);
                html += `
                    <div class="best-11-detail-card"
                         onclick="selectPlayer(${player.player_id})"
                         style="border-left: 4px solid ${teamColor.primary}">
                        <div class="detail-header">
                            <span class="detail-name">${player.player_name}</span>
                            <span class="detail-team">${player.team_name}</span>
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
    
    // 베스트 11 렌더링
    const content = document.getElementById('best-11-content');
    content.innerHTML = renderBest11();
}

// 전역 함수로 노출
window.renderTeamImprovements = renderTeamImprovements;
window.showBest11 = showBest11;
window.loadTeamImprovements = loadTeamImprovements;


// 전역 상태
let teamsData = {};
let currentTeam = null;
let currentPlayer = null;

// 데이터 로딩
async function loadData() {
    try {
        const response = await fetch('data/teams_data.json');
        if (!response.ok) {
            throw new Error('데이터를 불러올 수 없습니다.');
        }
        teamsData = await response.json();
        renderTeams();
    } catch (error) {
        console.error('Error loading data:', error);
        document.getElementById('team-grid').innerHTML = 
            '<div class="error">데이터를 불러오는 중 오류가 발생했습니다.</div>';
    }
}

// 팀 목록 렌더링
function renderTeams() {
    const teamGrid = document.getElementById('team-grid');
    const teams = Object.values(teamsData);
    
    if (teams.length === 0) {
        teamGrid.innerHTML = '<div class="error">팀 데이터가 없습니다.</div>';
        return;
    }
    
    teamGrid.innerHTML = teams.map(team => {
        const logoUrl = getTeamLogo(team.team_name);
        const fallbackUrl = fallbackLogos[team.team_name] || logoUrl;
        const teamColor = getTeamColor(team.team_name);
        return `
        <div class="team-card" onclick="selectTeam('${team.team_name}')" 
             style="background: linear-gradient(135deg, ${teamColor.primary} 0%, ${teamColor.secondary} 100%); 
                    color: ${teamColor.text};"
             data-team-name="${team.team_name}">
            <img src="${logoUrl}" alt="${team.team_name}" class="team-logo" 
                 onerror="this.onerror=null; this.src='${fallbackUrl}'; this.onerror=function(){this.style.display='none';}">
            <h3>${team.team_name}</h3>
            <div class="player-count">${team.players.length}명의 선수</div>
        </div>
    `;
    }).join('');
}

// 팀 선택
function selectTeam(teamName) {
    currentTeam = teamsData[teamName];
    if (!currentTeam) return;
    
    // 팀 색상 적용
    const teamColor = getTeamColor(teamName);
    applyTeamColorTheme(teamColor);
    
    // 섹션 전환
    document.getElementById('team-selection').classList.add('hidden');
    document.getElementById('player-list').classList.remove('hidden');
    document.getElementById('player-detail').classList.add('hidden');
    document.getElementById('team-analysis').classList.add('hidden');
    
    // 팀 이름 및 로고 표시
    const teamHeader = document.getElementById('team-name-header');
    const logoUrl = getTeamLogo(currentTeam.team_name);
    const fallbackUrl = fallbackLogos[currentTeam.team_name] || logoUrl;
    teamHeader.innerHTML = `
        <img src="${logoUrl}" alt="${currentTeam.team_name}" class="team-logo-small" 
             onerror="this.onerror=null; this.src='${fallbackUrl}'; this.onerror=function(){this.style.display='none';}">
        ${currentTeam.team_name}
    `;
    
    // 섹션에 팀 테마 적용
    const playerListSection = document.getElementById('player-list');
    if (playerListSection) {
        playerListSection.classList.add('team-themed');
    }
    
    // 선수 목록 렌더링
    renderPlayers();
}

// 정렬 기준 (전역 변수)
let currentSortOrder = 'fit_score';

// 정렬 기준 변경
window.changeSortOrder = function(sortBy) {
    currentSortOrder = sortBy;
    renderPlayers();
};

// 선수 목록 렌더링
function renderPlayers() {
    const playerGrid = document.getElementById('player-grid');
    const players = currentTeam.players;
    
    // 정렬 기준에 따라 정렬
    let sortedPlayers = [...players];
    switch(currentSortOrder) {
        case 'war':
            sortedPlayers.sort((a, b) => {
                const warA = a.war || 0;
                const warB = b.war || 0;
                return warB - warA; // 내림차순
            });
            break;
        case 'game_count':
            sortedPlayers.sort((a, b) => b.game_count - a.game_count);
            break;
        case 'team_win_rate':
            sortedPlayers.sort((a, b) => {
                const rateA = a.team_win_rate || 0;
                const rateB = b.team_win_rate || 0;
                return rateB - rateA;
            });
            break;
        case 'fit_score':
        default:
            sortedPlayers.sort((a, b) => b.fit_score - a.fit_score);
            break;
    }
    
    playerGrid.innerHTML = sortedPlayers.map(player => {
        const war = player.war || 0;
        const warDisplay = war !== 0 ? `${war > 0 ? '+' : ''}${(war * 100).toFixed(1)}%p` : 'N/A';
        
        return `
        <div class="player-card" onclick="selectPlayer(${player.player_id})">
            <h3>${player.player_name}</h3>
            <div>
                <span class="position">${player.position}</span>
                <span class="role">${player.role}</span>
            </div>
            <div class="fit-score">${player.fit_score}점</div>
            <div class="stats">
                <span>${player.game_count}경기</span>
                <span>${player.event_count.toLocaleString()}이벤트</span>
            </div>
            ${war !== 0 ? `<div class="war-stat">WAR: ${warDisplay}</div>` : ''}
        </div>
    `}).join('');
    
    // 정렬 기준에 맞게 셀렉트박스 업데이트
    const sortSelect = document.getElementById('sort-select');
    if (sortSelect) {
        sortSelect.value = currentSortOrder;
    }
}

// 팀 색상 테마 적용
function applyTeamColorTheme(teamColor) {
    document.documentElement.style.setProperty('--team-primary', teamColor.primary);
    document.documentElement.style.setProperty('--team-secondary', teamColor.secondary);
    document.documentElement.style.setProperty('--team-text', teamColor.text);
    
    // 배경 그라데이션 적용
    document.body.style.background = `linear-gradient(135deg, ${teamColor.primary}15 0%, ${teamColor.secondary}15 100%)`;
}

// 선수 선택 (전역 함수로 노출)
window.selectPlayer = function(playerId) {
    // 현재 팀에서 선수 찾기
    let player = currentTeam ? currentTeam.players.find(p => p.player_id === playerId) : null;
    let playerTeam = currentTeam;
    
    // 현재 팀에 없으면 모든 팀에서 찾기 (베스트 11 등에서 호출된 경우)
    if (!player) {
        for (const teamName in teamsData) {
            const team = teamsData[teamName];
            const foundPlayer = team.players.find(p => p.player_id === playerId);
            if (foundPlayer) {
                player = foundPlayer;
                playerTeam = team;
                break;
            }
        }
    }
    
    if (!player || !playerTeam) {
        console.warn('선수를 찾을 수 없습니다:', playerId);
        return;
    }
    
    // 선수가 속한 팀을 현재 팀으로 설정
    currentTeam = playerTeam;
    currentPlayer = player;
    selectedComparisonPlayers = []; // 비교 목록 초기화
    
    // 팀 색상 적용
    const teamColor = getTeamColor(currentTeam.team_name);
    applyTeamColorTheme(teamColor);
    
    // 섹션 전환
    document.getElementById('team-selection').classList.add('hidden');
    document.getElementById('player-list').classList.add('hidden');
    document.getElementById('player-detail').classList.remove('hidden');
    document.getElementById('team-analysis').classList.add('hidden');
    const best11Section = document.getElementById('best-11');
    if (best11Section) {
        best11Section.classList.add('hidden');
    }
    
    // 선수 이름 표시
    document.getElementById('player-name-header').textContent = player.player_name;
    
    // 섹션에 팀 테마 적용
    const playerDetailSection = document.getElementById('player-detail');
    if (playerDetailSection) {
        playerDetailSection.classList.add('team-themed');
    }
    
    // 선수 상세 정보 렌더링
    renderPlayerDetail();
};

// 기존 함수도 유지 (내부 호출용)
function selectPlayerInternal(playerId) {
    window.selectPlayer(playerId);
}

// 선수 상세 정보 렌더링
async function renderPlayerDetail() {
    const content = document.getElementById('player-detail-content');
    const p = currentPlayer;
    const details = p.score_details;
    
    // 향상된 데이터 로드 시도
    let enhancedData = null;
    try {
        const response = await fetch('data/teams_data_enhanced.json');
        if (response.ok) {
            enhancedData = await response.json();
            const teamData = enhancedData[currentTeam.team_name];
            if (teamData) {
                const enhancedPlayer = teamData.players.find(pl => pl.player_id === p.player_id);
                if (enhancedPlayer) {
                    p.enhanced = enhancedPlayer;
                }
            }
        }
    } catch (e) {
        console.log('Enhanced data not available');
    }
    
    content.innerHTML = `
        <div class="detail-card">
            <h3>기본 정보</h3>
            <div class="detail-row">
                <span class="detail-label">포지션</span>
                <span class="detail-value">${p.position}</span>
            </div>
            <div class="detail-row">
                <span class="detail-label">롤 (스타일)</span>
                <span class="detail-value">${p.role}</span>
            </div>
            <div class="detail-row">
                <span class="detail-label">경기 수</span>
                <span class="detail-value">${p.game_count}경기</span>
            </div>
            <div class="detail-row">
                <span class="detail-label">이벤트 수</span>
                <span class="detail-value">${p.event_count.toLocaleString()}개</span>
            </div>
            <div class="detail-row">
                <span class="detail-label">팀 승률 (출전 경기)</span>
                <span class="detail-value">${(p.team_win_rate * 100).toFixed(1)}%</span>
            </div>
        </div>
        
        <div class="detail-card">
            <h3>롤 적합도 점수</h3>
            <div class="score-breakdown">
                <div class="score-item">
                    <div class="label">종합 점수</div>
                    <div class="value">${p.fit_score}점</div>
                </div>
                <div class="score-item">
                    <div class="label">원점수</div>
                    <div class="value">${details.raw_score}점</div>
                </div>
                <div class="score-item">
                    <div class="label">신뢰도</div>
                    <div class="value">${(details.confidence * 100).toFixed(1)}%</div>
                </div>
                <div class="score-item">
                    <div class="label">코사인 유사도</div>
                    <div class="value">${details.cosine_score}점</div>
                </div>
                <div class="score-item">
                    <div class="label">유클리드 거리 점수</div>
                    <div class="value">${details.euclidean_score}점</div>
                </div>
                <div class="score-item">
                    <div class="label">경기 수 보너스</div>
                    <div class="value">${details.game_bonus > 0 ? '+' : ''}${details.game_bonus}점</div>
                </div>
                <div class="score-item">
                    <div class="label">팀 승률 기여도</div>
                    <div class="value">${details.win_rate_bonus > 0 ? '+' : ''}${details.win_rate_bonus}점</div>
                </div>
            </div>
        </div>
        
        ${p.enhanced ? `
        <div class="detail-card">
            <h3>능력치 비교 (레이더 차트)</h3>
            <div class="comparison-controls">
                <div class="search-box">
                    <input type="text" id="player-search" placeholder="선수 이름 검색..." class="search-input">
                    <button class="btn btn-primary" onclick="searchAndAddPlayer()">검색</button>
                </div>
                <div class="top-players-list">
                    <label>또는 리그 내 최상위 선수 선택:</label>
                    <select id="top-players-select" class="player-select" onchange="selectTopPlayer()">
                        <option value="">선택하세요...</option>
                    </select>
                </div>
                <div id="selected-comparison-players" class="selected-players"></div>
            </div>
            <div class="radar-chart-container">
                <canvas id="radar-chart"></canvas>
            </div>
        </div>
        
        <div class="detail-card">
            <h3>패스 네트워크</h3>
            <div id="pass-network"></div>
        </div>
        
        <div class="detail-card">
            <h3>전술 패턴 분석</h3>
            <div id="tactical-patterns">
                <p>전술 패턴 데이터 로딩 중...</p>
            </div>
        </div>
        ` : ''}
    `;
    
    // 시각화 생성
    if (p.enhanced) {
        setTimeout(() => {
            // 상위 선수 목록 로드
            loadTopPlayersForComparison(p);
            
            if (p.enhanced.detailed_profile) {
                createRadarChart(p, []);
            }
            if (p.enhanced.pass_network) {
                createPassNetwork(p);
            }
            
            // 선수별 전술 패턴 표시 (해당 선수가 포함된 패턴만)
            loadPlayerTacticalPatterns(currentTeam.team_name, p.player_id);
        }, 100);
    }
}

// 선수별 전술 패턴 로드 및 표시 (해당 선수가 포함된 패턴만)
async function loadPlayerTacticalPatterns(teamName, playerId) {
    const container = document.getElementById('tactical-patterns');
    if (!container) return;
    
    try {
        const response = await fetch('data/teams_data_enhanced.json');
        if (!response.ok) {
            container.innerHTML = '<p>전술 패턴 데이터를 불러올 수 없습니다.</p>';
            return;
        }
        
        const enhancedData = await response.json();
        const teamData = enhancedData[teamName];
        
        if (!teamData || !teamData.tactical_patterns) {
            container.innerHTML = '<p>전술 패턴 데이터가 아직 생성되지 않았습니다.<br>분석 스크립트를 실행하여 파생변수를 생성해주세요.</p>';
            return;
        }
        
        const allPatterns = teamData.tactical_patterns;
        // 선수별 필터링
        const filteredPatterns = filterPatternsByPlayer(allPatterns, playerId);
        renderPlayerTacticalPatterns(container, filteredPatterns, playerId);
    } catch (e) {
        console.error('Error loading player tactical patterns:', e);
        container.innerHTML = '<p>전술 패턴 데이터를 불러오는 중 오류가 발생했습니다.</p>';
    }
}

// 전술 패턴을 선수별로 필터링
function filterPatternsByPlayer(patterns, playerId) {
    const filtered = {};
    
    // 삼각형 패스 패턴
    if (patterns.triangle_passing && patterns.triangle_passing.triangles) {
        filtered.triangle_passing = {
            ...patterns.triangle_passing,
            triangles: patterns.triangle_passing.triangles.filter(t => 
                t.players && t.players.includes(playerId)
            )
        };
    }
    
    // 공격 전개 경로
    if (patterns.attacking_progression && patterns.attacking_progression.paths) {
        filtered.attacking_progression = {
            ...patterns.attacking_progression,
            paths: patterns.attacking_progression.paths.filter(p => 
                p.passer === playerId || p.receiver === playerId
            )
        };
    }
    
    // 사이드 체인지 패턴
    if (patterns.side_switch && patterns.side_switch.switches) {
        filtered.side_switch = {
            ...patterns.side_switch,
            switches: patterns.side_switch.switches.filter(s => 
                s.passer === playerId || s.receiver === playerId
            )
        };
    }
    
    // 역습 패턴
    if (patterns.counter_attack && patterns.counter_attack.counter_attacks) {
        filtered.counter_attack = {
            ...patterns.counter_attack,
            counter_attacks: patterns.counter_attack.counter_attacks.filter(c => 
                c.passer === playerId || c.receiver === playerId
            )
        };
    }
    
    // 듀오 효과성
    if (patterns.duo_effectiveness && patterns.duo_effectiveness.duos) {
        filtered.duo_effectiveness = {
            ...patterns.duo_effectiveness,
            duos: patterns.duo_effectiveness.duos.filter(d => 
                d.player1 === playerId || d.player2 === playerId
            )
        };
    }
    
    // 클러스터 효과성
    if (patterns.cluster_effectiveness && patterns.cluster_effectiveness.clusters) {
        filtered.cluster_effectiveness = {
            ...patterns.cluster_effectiveness,
            clusters: patterns.cluster_effectiveness.clusters.filter(c => 
                c.players && c.players.includes(playerId)
            )
        };
    }
    
    return filtered;
}

// 전술 패턴 로드 및 표시 (팀 전체 - 팀 분석 페이지용)
async function loadTacticalPatterns(teamName) {
    const container = document.getElementById('tactical-patterns');
    if (!container) return;
    
    try {
        const response = await fetch('data/teams_data_enhanced.json');
        if (!response.ok) {
            container.innerHTML = '<p>전술 패턴 데이터를 불러올 수 없습니다.</p>';
            return;
        }
        
        const enhancedData = await response.json();
        const teamData = enhancedData[teamName];
        
        if (!teamData || !teamData.tactical_patterns) {
            container.innerHTML = '<p>전술 패턴 데이터가 아직 생성되지 않았습니다.<br>분석 스크립트를 실행하여 파생변수를 생성해주세요.</p>';
            return;
        }
        
        const patterns = teamData.tactical_patterns;
        renderTacticalPatterns(container, patterns);
    } catch (e) {
        console.error('Error loading tactical patterns:', e);
        container.innerHTML = '<p>전술 패턴 데이터를 불러오는 중 오류가 발생했습니다.</p>';
    }
}

// 선수별 전술 패턴 렌더링 (인포그래픽 포함)
function renderPlayerTacticalPatterns(container, patterns, playerId) {
    let html = '<div class="player-tactical-patterns">';
    html += '<p class="info-text">이 선수가 포함된 전술 패턴만 표시됩니다.</p>';
    
    // 각 패턴 타입별로 데이터 확인
    const hasAnyPattern = Object.keys(patterns).some(key => {
        const pattern = patterns[key];
        if (key === 'triangle_passing' && pattern.triangles && pattern.triangles.length > 0) return true;
        if (key === 'attacking_progression' && pattern.paths && pattern.paths.length > 0) return true;
        if (key === 'side_switch' && pattern.switches && pattern.switches.length > 0) return true;
        if (key === 'counter_attack' && pattern.counter_attacks && pattern.counter_attacks.length > 0) return true;
        if (key === 'duo_effectiveness' && pattern.duos && pattern.duos.length > 0) return true;
        if (key === 'cluster_effectiveness' && pattern.clusters && pattern.clusters.length > 0) return true;
        return false;
    });
    
    if (!hasAnyPattern) {
        html += '<p>이 선수가 포함된 전술 패턴이 없습니다.</p>';
        html += '</div>';
        container.innerHTML = html;
        return;
    }
    
    // 인포그래픽 시각화 포함하여 렌더링
    html += renderPlayerTacticalPatternsWithVisualization(patterns, playerId);
    html += '</div>';
    container.innerHTML = html;
    
    // 시각화 생성 (requestAnimationFrame 사용하여 성능 개선)
    requestAnimationFrame(() => {
        createPlayerTacticalVisualizations(patterns, playerId);
    });
}

// 선수별 전술 패턴 인포그래픽 렌더링
function renderPlayerTacticalPatternsWithVisualization(patterns, playerId) {
    let html = '';
    
    // 듀오 효과성 시각화
    if (patterns.duo_effectiveness && patterns.duo_effectiveness.duos && patterns.duo_effectiveness.duos.length > 0) {
        html += '<div class="tactical-section">';
        html += '<h4>듀오 효과성</h4>';
        html += `<p>총 ${patterns.duo_effectiveness.duos.length}개의 효과적인 듀오 발견</p>`;
        html += '<div id="player-duo-visualization" class="tactical-visualization"></div>';
        html += '</div>';
    }
    
    // 클러스터 효과성 시각화
    if (patterns.cluster_effectiveness && patterns.cluster_effectiveness.clusters && patterns.cluster_effectiveness.clusters.length > 0) {
        html += '<div class="tactical-section">';
        html += '<h4>클러스터 효과성</h4>';
        html += `<p>총 ${patterns.cluster_effectiveness.clusters.length}개의 효과적인 클러스터 발견</p>`;
        html += '<div id="player-cluster-visualization" class="tactical-visualization"></div>';
        html += '</div>';
    }
    
    // 나머지는 텍스트로 표시
    html += renderTacticalPatternsContent(patterns);
    
    return html;
}

// 선수별 전술 패턴 시각화 생성
function createPlayerTacticalVisualizations(patterns, playerId) {
    // 향상된 데이터 로드 (팀 정보 포함)
    fetch('data/teams_data_enhanced.json')
        .then(response => response.json())
        .then(enhancedData => {
            const teamData = enhancedData[currentTeam.team_name];
            
            // 듀오 효과성 시각화
            if (patterns.duo_effectiveness && patterns.duo_effectiveness.duos) {
                const container = document.getElementById('player-duo-visualization');
                if (container) {
                    createDuoEffectivenessChart(container, patterns.duo_effectiveness.duos, teamData);
                }
            }
            
            // 클러스터 효과성 시각화
            if (patterns.cluster_effectiveness && patterns.cluster_effectiveness.clusters) {
                const container = document.getElementById('player-cluster-visualization');
                if (container) {
                    createClusterEffectivenessChart(container, patterns.cluster_effectiveness.clusters, teamData);
                }
            }
        })
        .catch(e => {
            console.error('Error loading enhanced data for visualizations:', e);
            // 폴백: 팀 데이터 없이도 작동
            if (patterns.duo_effectiveness && patterns.duo_effectiveness.duos) {
                const container = document.getElementById('player-duo-visualization');
                if (container) {
                    createDuoEffectivenessChart(container, patterns.duo_effectiveness.duos);
                }
            }
            if (patterns.cluster_effectiveness && patterns.cluster_effectiveness.clusters) {
                const container = document.getElementById('player-cluster-visualization');
                if (container) {
                    createClusterEffectivenessChart(container, patterns.cluster_effectiveness.clusters);
                }
            }
        });
}

// 듀오 효과성 인포그래픽 생성 (공통 함수)
function createDuoEffectivenessChart(container, duos, teamData = null) {
    // 최소 경기 수 필터링 및 인포그래픽 생성
    if (typeof createDuoEffectivenessInfographic === 'function') {
        createDuoEffectivenessInfographic(container, duos, teamData || currentTeam);
    } else {
        // 폴백: 최소 경기 수 필터링만 적용
        const significantDuos = duos.filter(d => d.games_together >= 10);
        if (significantDuos.length === 0) {
            container.innerHTML = '<div class="insufficient-data"><p>통계적 유의성을 위한 충분한 데이터가 없습니다.<br>최소 10경기 이상 함께 뛴 듀오만 표시됩니다.</p></div>';
            return;
        }
        // 인포그래픽 함수가 로드되지 않은 경우 간단한 메시지 표시
        container.innerHTML = '<div class="insufficient-data"><p>인포그래픽을 로드하는 중입니다...</p></div>';
    }
}

// 클러스터 효과성 인포그래픽 생성 (공통 함수)
function createClusterEffectivenessChart(container, clusters, teamData = null) {
    // 최소 경기 수 필터링 및 인포그래픽 생성
    if (typeof createClusterEffectivenessInfographic === 'function') {
        createClusterEffectivenessInfographic(container, clusters, teamData || currentTeam);
    } else {
        // 폴백: 최소 경기 수 필터링만 적용
        const significantClusters = clusters.filter(c => c.active_games >= 10);
        if (significantClusters.length === 0) {
            container.innerHTML = '<div class="insufficient-data"><p>통계적 유의성을 위한 충분한 데이터가 없습니다.<br>최소 10경기 이상 활성화된 클러스터만 표시됩니다.</p></div>';
            return;
        }
        // 인포그래픽 함수가 로드되지 않은 경우 간단한 메시지 표시
        container.innerHTML = '<div class="insufficient-data"><p>인포그래픽을 로드하는 중입니다...</p></div>';
    }
}

// 전술 패턴 렌더링 (팀 전체)
function renderTacticalPatterns(container, patterns) {
    container.innerHTML = renderTacticalPatternsContent(patterns);
}

// 전술 패턴 내용 렌더링 (공통 함수)
function renderTacticalPatternsContent(patterns) {
    let html = '';
    
    // 삼각형 패스 패턴
    if (patterns.triangle_passing && patterns.triangle_passing.triangles) {
        const triangleData = patterns.triangle_passing;
        html += '<div class="tactical-section">';
        html += '<h4>삼각형 패스 패턴</h4>';
        html += `<p>총 ${triangleData.total_triangles || 0}개의 삼각형 패턴 발견 (고유: ${triangleData.unique_triangles || 0}개)</p>`;
        if (triangleData.validation) {
            html += `<p class="validation-info">검증률: ${(triangleData.validation.validation_rate * 100).toFixed(1)}% (${triangleData.validation.valid_count}/${triangleData.validation.total_count})</p>`;
        }
        html += '<div class="pattern-list">';
        
        triangleData.triangles.slice(0, 5).forEach((triangle, idx) => {
            html += `<div class="pattern-item">`;
            html += `<strong>${idx + 1}. ${triangle.player_names.join(' → ')}</strong>`;
            html += `<div class="pattern-stats">`;
            html += `<span>빈도: ${triangle.frequency}회</span>`;
            html += `<span>성공률: ${(triangle.success_rate * 100).toFixed(1)}%</span>`;
            html += `<span>평균 시간: ${triangle.avg_time.toFixed(1)}초</span>`;
            html += `</div>`;
            html += `</div>`;
        });
        
        html += '</div></div>';
    }
    
    // 공격 전개 경로
    if (patterns.attacking_progression && patterns.attacking_progression.paths && patterns.attacking_progression.paths.length > 0) {
        const progressionData = patterns.attacking_progression;
        const pathCount = progressionData.paths.length;
        const totalPaths = progressionData.total_paths || pathCount;
        
        html += '<div class="tactical-section">';
        html += '<h4>공격 전개 경로</h4>';
        html += `<p>총 ${totalPaths}개의 공격 전개 경로 발견 (표시: ${pathCount}개)</p>`;
        if (progressionData.validation) {
            html += `<p class="validation-info">검증률: ${(progressionData.validation.validation_rate * 100).toFixed(1)}% (${progressionData.validation.valid_count}/${progressionData.validation.total_count})</p>`;
        }
        html += '<div class="pattern-list">';
        
        progressionData.paths.slice(0, 5).forEach((path, idx) => {
            html += `<div class="pattern-item">`;
            html += `<strong>${idx + 1}. ${path.passer_name} → ${path.receiver_name}</strong>`;
            html += `<div class="pattern-stats">`;
            html += `<span>${path.from_zone} → ${path.to_zone}</span>`;
            html += `<span>빈도: ${path.frequency}회</span>`;
            html += `<span>성공률: ${(path.success_rate * 100).toFixed(1)}%</span>`;
            if (path.goal_contribution > 0) {
                html += `<span class="highlight">골 기여: ${path.goal_contribution}회</span>`;
            }
            html += `</div>`;
            html += `</div>`;
        });
        
        html += '</div></div>';
    } else if (patterns.attacking_progression && (!patterns.attacking_progression.paths || patterns.attacking_progression.paths.length === 0)) {
        // 데이터는 있지만 경로가 없는 경우
        html += '<div class="tactical-section">';
        html += '<h4>공격 전개 경로</h4>';
        html += '<p>공격 전개 경로 데이터가 없습니다.</p>';
        html += '</div>';
    }
    
    // 사이드 체인지 패턴
    if (patterns.side_switch && patterns.side_switch.switches) {
        const switchData = patterns.side_switch;
        html += '<div class="tactical-section">';
        html += '<h4>사이드 체인지 패턴</h4>';
        html += `<p>총 ${switchData.total_switches || 0}개의 사이드 체인지 발견</p>`;
        if (switchData.validation) {
            html += `<p class="validation-info">검증률: ${(switchData.validation.validation_rate * 100).toFixed(1)}% (${switchData.validation.valid_count}/${switchData.validation.total_count})</p>`;
        }
        html += '<div class="pattern-list">';
        
        switchData.switches.slice(0, 5).forEach((switch_pattern, idx) => {
            html += `<div class="pattern-item">`;
            html += `<strong>${idx + 1}. ${switch_pattern.passer_name} → ${switch_pattern.receiver_name}</strong>`;
            html += `<div class="pattern-stats">`;
            html += `<span>${switch_pattern.from_side} → ${switch_pattern.to_side}</span>`;
            html += `<span>빈도: ${switch_pattern.frequency}회</span>`;
            html += `<span>성공률: ${(switch_pattern.success_rate * 100).toFixed(1)}%</span>`;
            if (switch_pattern.attack_contribution > 0) {
                html += `<span class="highlight">공격 기여: ${switch_pattern.attack_contribution}회</span>`;
            }
            html += `</div>`;
            html += `</div>`;
        });
        
        html += '</div></div>';
    }
    
    // 역습 패턴
    if (patterns.counter_attack && patterns.counter_attack.counter_attacks) {
        const counterData = patterns.counter_attack;
        html += '<div class="tactical-section">';
        html += '<h4>역습 패턴</h4>';
        html += `<p>총 ${counterData.total_counter_attacks || 0}개의 역습 발견</p>`;
        if (counterData.validation) {
            html += `<p class="validation-info">검증률: ${(counterData.validation.validation_rate * 100).toFixed(1)}% (${counterData.validation.valid_count}/${counterData.validation.total_count})</p>`;
        }
        html += '<div class="pattern-list">';
        
        counterData.counter_attacks.slice(0, 5).forEach((counter, idx) => {
            html += `<div class="pattern-item">`;
            html += `<strong>${idx + 1}. ${counter.passer_name} → ${counter.receiver_name}</strong>`;
            html += `<div class="pattern-stats">`;
            html += `<span>빈도: ${counter.frequency}회</span>`;
            html += `<span>평균 패스 수: ${counter.avg_pass_count.toFixed(1)}개</span>`;
            html += `<span>평균 시간: ${counter.avg_time.toFixed(1)}초</span>`;
            if (counter.goal_contribution > 0) {
                html += `<span class="highlight">골 기여: ${counter.goal_contribution}회</span>`;
            }
            html += `</div>`;
            html += `</div>`;
        });
        
        html += '</div></div>';
    }
    
    // 듀오 효과성
    if (patterns.duo_effectiveness && patterns.duo_effectiveness.duos) {
        const duoData = patterns.duo_effectiveness;
        html += '<div class="tactical-section">';
        html += '<h4>듀오 효과성</h4>';
        html += `<p>총 ${duoData.total_duos || 0}개의 효과적인 듀오 발견</p>`;
        if (duoData.validation) {
            html += `<p class="validation-info">검증률: ${(duoData.validation.validation_rate * 100).toFixed(1)}% (${duoData.validation.valid_count}/${duoData.validation.total_count})</p>`;
        }
        html += '<div class="pattern-list">';
        
        // 최소 경기 수 필터링 (10경기 이상)
        const significantDuos = duoData.duos.filter(d => d.games_together >= 10);
        
        if (significantDuos.length === 0) {
            html += '<p class="insufficient-data-text">통계적 유의성을 위한 충분한 데이터가 없습니다. (최소 10경기 이상 필요)</p>';
        } else {
            significantDuos.slice(0, 5).forEach((duo, idx) => {
                html += `<div class="pattern-item">`;
                html += `<strong>${idx + 1}. ${duo.player1_name} + ${duo.player2_name}</strong>`;
                html += `<div class="pattern-stats">`;
                html += `<span>함께 뛴 경기: ${duo.games_together}경기</span>`;
                html += `<span>승률: ${(duo.win_rate * 100).toFixed(1)}%</span>`;
                html += `<span>평균 득점: ${duo.avg_goals_for.toFixed(1)}</span>`;
                html += `<span>평균 실점: ${duo.avg_goals_against.toFixed(1)}</span>`;
                html += `<span>패스 빈도: ${duo.pass_frequency}회</span>`;
                html += `</div>`;
                html += `</div>`;
            });
        }
        
        html += '</div></div>';
    }
    
    // 클러스터 효과성
    if (patterns.cluster_effectiveness && patterns.cluster_effectiveness.clusters) {
        const clusterData = patterns.cluster_effectiveness;
        html += '<div class="tactical-section">';
        html += '<h4>클러스터 효과성</h4>';
        html += `<p>총 ${clusterData.total_clusters || 0}개의 효과적인 클러스터 발견</p>`;
        if (clusterData.validation) {
            html += `<p class="validation-info">검증률: ${(clusterData.validation.validation_rate * 100).toFixed(1)}% (${clusterData.validation.valid_count}/${clusterData.validation.total_count})</p>`;
        }
        html += '<div class="pattern-list">';
        
        // 최소 경기 수 필터링 (10경기 이상)
        const significantClusters = clusterData.clusters.filter(c => c.active_games >= 10);
        
        if (significantClusters.length === 0) {
            html += '<p class="insufficient-data-text">통계적 유의성을 위한 충분한 데이터가 없습니다. (최소 10경기 이상 필요)</p>';
        } else {
            significantClusters.slice(0, 5).forEach((cluster, idx) => {
                html += `<div class="pattern-item">`;
                html += `<strong>${idx + 1}. ${cluster.player_names.join(', ')}</strong>`;
                html += `<div class="pattern-stats">`;
                html += `<span>크기: ${cluster.cluster_size}명</span>`;
                html += `<span>활성 경기: ${cluster.active_games}경기</span>`;
                html += `<span>승률: ${(cluster.win_rate * 100).toFixed(1)}%</span>`;
                html += `<span>응집도: ${cluster.cohesion.toFixed(1)}</span>`;
                html += `<span>패스 빈도: ${cluster.cluster_pass_count}회</span>`;
                html += `</div>`;
                html += `</div>`;
            });
        }
        
        html += '</div></div>';
    }
    
    if (html === '') {
        html = '<p>전술 패턴 데이터가 없습니다.</p>';
    }
    
    return html;
}

// 상위 선수 목록 로드
function loadTopPlayersForComparison(currentPlayer) {
    const select = document.getElementById('top-players-select');
    if (!select) return;
    
    // 모든 팀에서 같은 포지션/롤의 선수 찾기
    const candidates = [];
    
    Object.values(teamsData).forEach(team => {
        team.players.forEach(player => {
            if (player.position === currentPlayer.position && 
                player.role === currentPlayer.role &&
                player.player_id !== currentPlayer.player_id) {
                candidates.push({
                    player_id: player.player_id,
                    player_name: player.player_name,
                    team_name: team.team_name,
                    fit_score: player.fit_score
                });
            }
        });
    });
    
    // 적합도 점수 순으로 정렬
    candidates.sort((a, b) => b.fit_score - a.fit_score);
    
    // 상위 10명만 표시
    select.innerHTML = '<option value="">선택하세요...</option>' +
        candidates.slice(0, 10).map(p => 
            `<option value="${p.player_id}" data-team="${p.team_name}">${p.player_name} (${p.team_name}) - ${p.fit_score}점</option>`
        ).join('');
}

// 상위 선수 선택
window.selectTopPlayer = function() {
    const select = document.getElementById('top-players-select');
    const playerId = parseFloat(select.value);
    if (!playerId) return;
    
    const teamName = select.options[select.selectedIndex].dataset.team;
    const playerName = select.options[select.selectedIndex].text.split(' (')[0];
    
    // 향상된 데이터에서 선수 찾기
    loadEnhancedPlayerData(playerId, teamName, playerName);
};

// 선수 검색
window.searchAndAddPlayer = function() {
    const searchInput = document.getElementById('player-search');
    const searchTerm = searchInput.value.trim();
    if (!searchTerm) return;
    
    // 모든 팀에서 선수 검색
    let foundPlayer = null;
    
    Object.values(teamsData).forEach(team => {
        const player = team.players.find(p => 
            p.player_name.includes(searchTerm)
        );
        if (player) {
            foundPlayer = { ...player, team_name: team.team_name };
        }
    });
    
    if (foundPlayer) {
        loadEnhancedPlayerData(foundPlayer.player_id, foundPlayer.team_name, foundPlayer.player_name);
        searchInput.value = '';
    } else {
        alert('선수를 찾을 수 없습니다.');
    }
};

// 향상된 선수 데이터 로드
async function loadEnhancedPlayerData(playerId, teamName, playerName) {
    try {
        const response = await fetch('data/teams_data_enhanced.json');
        if (!response.ok) return;
        
        const enhancedData = await response.json();
        const teamData = enhancedData[teamName];
        if (!teamData) return;
        
        const enhancedPlayer = teamData.players.find(p => p.player_id === playerId);
        if (enhancedPlayer && enhancedPlayer.detailed_profile) {
            // 비교 목록에 추가 (team_name 포함)
            selectedComparisonPlayers.push({
                player_id: playerId,
                player_name: playerName,
                team_name: teamName,
                profile: enhancedPlayer.detailed_profile,
                enhanced: enhancedPlayer
            });
            
            // UI 업데이트
            updateSelectedPlayersList();
            
            // 레이더 차트 업데이트
            if (currentPlayer) {
                createRadarChart(currentPlayer, selectedComparisonPlayers);
            }
        }
    } catch (e) {
        console.error('Error loading enhanced player data:', e);
    }
}

// 선택된 선수 목록 업데이트
function updateSelectedPlayersList() {
    const container = document.getElementById('selected-comparison-players');
    if (!container) return;
    
    if (selectedComparisonPlayers.length === 0) {
        container.innerHTML = '';
        return;
    }
    
    container.innerHTML = '<strong>비교 중인 선수:</strong> ' +
        selectedComparisonPlayers.map((p, idx) => {
            const teamColor = getTeamColor(p.team_name || '');
            return `<span class="selected-player-tag" style="background: ${teamColor.primary}; color: ${teamColor.text};">${p.player_name} (${p.team_name || ''})
                <button onclick="removeComparisonPlayer(${idx})" class="remove-btn">×</button>
            </span>`;
        }).join(' ');
}

// 비교 선수 제거
window.removeComparisonPlayer = function(index) {
    selectedComparisonPlayers.splice(index, 1);
    updateSelectedPlayersList();
    if (currentPlayer) {
        createRadarChart(currentPlayer, selectedComparisonPlayers);
    }
};

// 뒤로가기 버튼
document.getElementById('back-to-teams').addEventListener('click', () => {
    document.getElementById('team-selection').classList.remove('hidden');
    document.getElementById('player-list').classList.add('hidden');
    document.getElementById('player-detail').classList.add('hidden');
    document.getElementById('team-analysis').classList.add('hidden');
    currentTeam = null;
    currentPlayer = null;
});

document.getElementById('back-to-players').addEventListener('click', () => {
    document.getElementById('team-selection').classList.add('hidden');
    document.getElementById('player-list').classList.remove('hidden');
    document.getElementById('player-detail').classList.add('hidden');
    document.getElementById('team-analysis').classList.add('hidden');
    currentPlayer = null;
    
    // 팀 색상 유지
    if (currentTeam) {
        const teamColor = getTeamColor(currentTeam.team_name);
        applyTeamColorTheme(teamColor);
    }
});

// 팀 분석 보기 버튼
document.getElementById('view-team-analysis').addEventListener('click', () => {
    renderTeamAnalysis();
});

// 팀 분석에서 선수 목록으로 돌아가기
document.getElementById('back-to-players-from-analysis').addEventListener('click', () => {
    document.getElementById('team-selection').classList.add('hidden');
    document.getElementById('player-list').classList.remove('hidden');
    document.getElementById('player-detail').classList.add('hidden');
    document.getElementById('team-analysis').classList.add('hidden');
});

// 베스트 11 보기 버튼
document.getElementById('view-best-11').addEventListener('click', () => {
    showBest11();
});

// 베스트 11에서 팀 목록으로 돌아가기
document.getElementById('back-to-teams-from-best11').addEventListener('click', () => {
    document.getElementById('team-selection').classList.remove('hidden');
    document.getElementById('player-list').classList.add('hidden');
    document.getElementById('player-detail').classList.add('hidden');
    document.getElementById('team-analysis').classList.add('hidden');
    document.getElementById('best-11').classList.add('hidden');
});

// 페이지 로드 시 개선점 데이터도 로딩
window.addEventListener('DOMContentLoaded', () => {
    loadData();
    loadTeamImprovements();
});

// 구현 과정 툴팁 함수
function showImplementationTooltip(event) {
    const modal = document.getElementById('info-modal');
    const modalBody = document.getElementById('modal-body');
    
    // 현재 섹션에 따라 다른 내용 표시
    const playerDetailSection = document.getElementById('player-detail');
    const teamAnalysisSection = document.getElementById('team-analysis');
    
    let content = '';
    
    if (!playerDetailSection.classList.contains('hidden')) {
        // 선수 상세 페이지
        content = getImplementationInfo('player-detail');
    } else if (!teamAnalysisSection.classList.contains('hidden')) {
        // 팀 분석 페이지
        content = getImplementationInfo('team-analysis');
    } else {
        // 기본 (팀 선택 또는 선수 목록)
        content = getImplementationInfo('default');
    }
    
    modalBody.innerHTML = content;
    modal.style.display = 'block';
    
    // 모달 닫기 이벤트 리스너
    const closeBtn = modal.querySelector('.close');
    if (closeBtn) {
        closeBtn.onclick = function() {
            modal.style.display = 'none';
        };
    }
    
    // 모달 외부 클릭 시 닫기
    window.onclick = function(event) {
        if (event.target === modal) {
            modal.style.display = 'none';
        }
    };
}

function hideImplementationTooltip() {
    const modal = document.getElementById('info-modal');
    modal.style.display = 'none';
}

// 전역 함수로 노출
window.showImplementationTooltip = showImplementationTooltip;
window.hideImplementationTooltip = hideImplementationTooltip;

// 페이지 로드 시 데이터 로딩 (이미 위에서 처리됨)


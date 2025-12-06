// 팀 분석 페이지 렌더링

async function renderTeamAnalysis() {
    if (!currentTeam) return;
    
    // 섹션 전환
    document.getElementById('team-selection').classList.add('hidden');
    document.getElementById('player-list').classList.add('hidden');
    document.getElementById('player-detail').classList.add('hidden');
    document.getElementById('team-analysis').classList.remove('hidden');
    
    const content = document.getElementById('team-analysis-content');
    const header = document.getElementById('team-analysis-header');
    
    const logoUrl = getTeamLogo(currentTeam.team_name);
    header.innerHTML = `
        <img src="${logoUrl}" alt="${currentTeam.team_name}" class="team-logo-small" 
             onerror="this.style.display='none'">
        ${currentTeam.team_name} 전술 분석
    `;
    
    content.innerHTML = '<div class="loading">전술 패턴 데이터 로딩 중...</div>';
    
    try {
        const response = await fetch('data/teams_data_enhanced.json');
        if (!response.ok) {
            content.innerHTML = '<div class="error">데이터를 불러올 수 없습니다.</div>';
            return;
        }
        
        const enhancedData = await response.json();
        const teamData = enhancedData[currentTeam.team_name];
        
        if (!teamData || !teamData.tactical_patterns) {
            content.innerHTML = '<div class="error">전술 패턴 데이터가 아직 생성되지 않았습니다.</div>';
            return;
        }
        
        const patterns = teamData.tactical_patterns;
        
        let html = '<div class="team-analysis-container">';
        
        // 팀 개선점 분석 섹션 추가
        html += '<div class="team-improvements-section">';
        html += '<h3>팀 개선점 및 추천 선수</h3>';
        html += renderTeamImprovements(currentTeam.team_name);
        html += '</div>';
        
        html += '<div class="tactical-patterns-section">';
        html += '<h3>팀 전술 패턴 분석</h3>';
        
        // 팀 전술 패턴 인포그래픽
        html += renderTeamTacticalVisualizations(patterns, teamData);
        
        html += '<div id="tactical-patterns"></div>';
        html += '</div>';
        html += '</div>';
        
        content.innerHTML = html;
        
        // 전술 패턴 렌더링 (팀 전체)
        const patternsContainer = document.getElementById('tactical-patterns');
        renderTacticalPatterns(patternsContainer, patterns);
        
        // 시각화 생성 (requestAnimationFrame 사용하여 성능 개선)
        requestAnimationFrame(() => {
            createTeamTacticalVisualizations(patterns, teamData);
        });
        
    } catch (e) {
        console.error('Error loading team analysis:', e);
        content.innerHTML = '<div class="error">데이터를 불러오는 중 오류가 발생했습니다.</div>';
    }
}

// 팀 전술 패턴 인포그래픽 렌더링
function renderTeamTacticalVisualizations(patterns, teamData) {
    let html = '<div class="team-tactical-visualizations">';
    
    // 듀오 효과성 시각화
    if (patterns.duo_effectiveness && patterns.duo_effectiveness.duos && patterns.duo_effectiveness.duos.length > 0) {
        html += '<div class="tactical-visualization-section">';
        html += '<h4>듀오 효과성 시각화</h4>';
        html += '<div id="team-duo-visualization" class="tactical-visualization"></div>';
        html += '</div>';
    }
    
    // 클러스터 효과성 시각화
    if (patterns.cluster_effectiveness && patterns.cluster_effectiveness.clusters && patterns.cluster_effectiveness.clusters.length > 0) {
        html += '<div class="tactical-visualization-section">';
        html += '<h4>클러스터 효과성 시각화</h4>';
        html += '<div id="team-cluster-visualization" class="tactical-visualization"></div>';
        html += '</div>';
    }
    
    html += '</div>';
    return html;
}

// 팀 전술 패턴 시각화 생성
function createTeamTacticalVisualizations(patterns, teamData) {
    // 듀오 효과성 시각화 (app.js의 공통 함수 사용)
    if (patterns.duo_effectiveness && patterns.duo_effectiveness.duos) {
        const container = document.getElementById('team-duo-visualization');
        if (container && typeof createDuoEffectivenessChart === 'function') {
            createDuoEffectivenessChart(container, patterns.duo_effectiveness.duos, teamData);
        }
    }
    
    // 클러스터 효과성 시각화 (app.js의 공통 함수 사용)
    if (patterns.cluster_effectiveness && patterns.cluster_effectiveness.clusters) {
        const container = document.getElementById('team-cluster-visualization');
        if (container && typeof createClusterEffectivenessChart === 'function') {
            createClusterEffectivenessChart(container, patterns.cluster_effectiveness.clusters, teamData);
        }
    }
}


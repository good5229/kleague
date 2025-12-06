// 축구 전술 인포그래픽 시각화
// 참고: Opta, StatsBomb, Wyscout 스타일

// 축구 필드 SVG 생성 (4-3-3 포메이션 기준)
function createFootballFieldSVG(width = 600, height = 400) {
    const svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
    svg.setAttribute('width', width);
    svg.setAttribute('height', height);
    svg.setAttribute('viewBox', '0 0 100 68');
    svg.style.background = '#2d5016';
    svg.style.borderRadius = '8px';
    
    // 필드 라인 (scaleFactor 적용)
    const baseWidth = 100;
    const baseHeight = 68;
    const fieldLines = [
        // 외곽 라인
        { x1: 0, y1: 0, x2: baseWidth * scaleFactor, y2: 0, stroke: '#fff', 'stroke-width': 0.3 * scaleFactor },
        { x1: 0, y1: baseHeight * scaleFactor, x2: baseWidth * scaleFactor, y2: baseHeight * scaleFactor, stroke: '#fff', 'stroke-width': 0.3 * scaleFactor },
        { x1: 0, y1: 0, x2: 0, y2: baseHeight * scaleFactor, stroke: '#fff', 'stroke-width': 0.3 * scaleFactor },
        { x1: baseWidth * scaleFactor, y1: 0, x2: baseWidth * scaleFactor, y2: baseHeight * scaleFactor, stroke: '#fff', 'stroke-width': 0.3 * scaleFactor },
        // 중앙 라인
        { x1: (baseWidth / 2) * scaleFactor, y1: 0, x2: (baseWidth / 2) * scaleFactor, y2: baseHeight * scaleFactor, stroke: '#fff', 'stroke-width': 0.3 * scaleFactor },
        // 중앙 서클
        { cx: (baseWidth / 2) * scaleFactor, cy: (baseHeight / 2) * scaleFactor, r: 9.15 * scaleFactor, fill: 'none', stroke: '#fff', 'stroke-width': 0.3 * scaleFactor },
        // 페널티 박스
        { x1: 0, y1: 13.84 * scaleFactor, x2: 16.5 * scaleFactor, y2: 13.84 * scaleFactor, stroke: '#fff', 'stroke-width': 0.3 * scaleFactor },
        { x1: 0, y1: 54.16 * scaleFactor, x2: 16.5 * scaleFactor, y2: 54.16 * scaleFactor, stroke: '#fff', 'stroke-width': 0.3 * scaleFactor },
        { x1: 16.5 * scaleFactor, y1: 13.84 * scaleFactor, x2: 16.5 * scaleFactor, y2: 54.16 * scaleFactor, stroke: '#fff', 'stroke-width': 0.3 * scaleFactor },
        { x1: baseWidth * scaleFactor, y1: 13.84 * scaleFactor, x2: (baseWidth - 16.5) * scaleFactor, y2: 13.84 * scaleFactor, stroke: '#fff', 'stroke-width': 0.3 * scaleFactor },
        { x1: baseWidth * scaleFactor, y1: 54.16 * scaleFactor, x2: (baseWidth - 16.5) * scaleFactor, y2: 54.16 * scaleFactor, stroke: '#fff', 'stroke-width': 0.3 * scaleFactor },
        { x1: (baseWidth - 16.5) * scaleFactor, y1: 13.84 * scaleFactor, x2: (baseWidth - 16.5) * scaleFactor, y2: 54.16 * scaleFactor, stroke: '#fff', 'stroke-width': 0.3 * scaleFactor },
        // 골 에어리어
        { x1: 0, y1: 24.66 * scaleFactor, x2: 5.5 * scaleFactor, y2: 24.66 * scaleFactor, stroke: '#fff', 'stroke-width': 0.3 * scaleFactor },
        { x1: 0, y1: 43.34 * scaleFactor, x2: 5.5 * scaleFactor, y2: 43.34 * scaleFactor, stroke: '#fff', 'stroke-width': 0.3 * scaleFactor },
        { x1: 5.5 * scaleFactor, y1: 24.66 * scaleFactor, x2: 5.5 * scaleFactor, y2: 43.34 * scaleFactor, stroke: '#fff', 'stroke-width': 0.3 * scaleFactor },
        { x1: baseWidth * scaleFactor, y1: 24.66 * scaleFactor, x2: (baseWidth - 5.5) * scaleFactor, y2: 24.66 * scaleFactor, stroke: '#fff', 'stroke-width': 0.3 * scaleFactor },
        { x1: baseWidth * scaleFactor, y1: 43.34 * scaleFactor, x2: (baseWidth - 5.5) * scaleFactor, y2: 43.34 * scaleFactor, stroke: '#fff', 'stroke-width': 0.3 * scaleFactor },
        { x1: (baseWidth - 5.5) * scaleFactor, y1: 24.66 * scaleFactor, x2: (baseWidth - 5.5) * scaleFactor, y2: 43.34 * scaleFactor, stroke: '#fff', 'stroke-width': 0.3 * scaleFactor }
    ];
    
    fieldLines.forEach(line => {
        const element = document.createElementNS('http://www.w3.org/2000/svg', 
            line.cx ? 'circle' : 'line');
        Object.keys(line).forEach(key => {
            element.setAttribute(key, line[key]);
        });
        svg.appendChild(element);
    });
    
    return svg;
}

// 포지션을 필드 좌표로 변환 (4-3-3 포메이션)
function getPositionCoordinates(position, formation = '4-3-3') {
    // 포지션별 기본 좌표 (x: 0-100, y: 0-68)
    const positions = {
        'GK': { x: 5, y: 34 },
        'CB': { x: 15, y: 20 },  // 왼쪽
        'CB': { x: 15, y: 48 },  // 오른쪽
        'LB': { x: 15, y: 10 },
        'RB': { x: 15, y: 58 },
        'CDM': { x: 30, y: 34 },
        'CM': { x: 35, y: 20 },  // 왼쪽
        'CM': { x: 35, y: 48 },  // 오른쪽
        'CAM': { x: 50, y: 34 },
        'LW': { x: 65, y: 15 },
        'RW': { x: 65, y: 53 },
        'ST': { x: 80, y: 34 }
    };
    
    return positions[position] || { x: 50, y: 34 };
}

// 듀오 효과성 인포그래픽 생성 (최적화)
function createDuoEffectivenessInfographic(container, duos, teamData) {
    container.innerHTML = '';
    
    // 최소 경기 수 필터링 (10경기 이상)
    const significantDuos = duos.filter(d => d.games_together >= 10);
    
    if (significantDuos.length === 0) {
        container.innerHTML = '<div class="insufficient-data"><p>통계적 유의성을 위한 충분한 데이터가 없습니다.<br>최소 10경기 이상 함께 뛴 듀오만 표시됩니다.</p></div>';
        return;
    }
    
    const topDuos = significantDuos.slice(0, 5);
    
    // DocumentFragment 사용 (성능 개선)
    const fragment = document.createDocumentFragment();
    
    // 각 듀오별 인포그래픽 생성
    topDuos.forEach((duo, idx) => {
        const duoCard = document.createElement('div');
        duoCard.className = 'duo-infographic-card';
        
        // 승률 게이지 차트
        const winRateGauge = createWinRateGauge(duo.win_rate, duo.games_together);
        
        // 필드 다이어그램 (크기 확대, scaleFactor 2.0으로 폰트 크기 유지)
        const fieldSVG = createFootballFieldSVG(800, 560, 2.0);
        
        // 선수 정보 가져오기
        const player1 = teamData.players.find(p => p.player_id === duo.player1);
        const player2 = teamData.players.find(p => p.player_id === duo.player2);
        const player1Pos = findPlayerPosition(duo.player1, teamData);
        const player2Pos = findPlayerPosition(duo.player2, teamData);
        
        // 같은 포지션인지 확인
        const samePosition = player1 && player2 && player1.position === player2.position;
        
        // DocumentFragment로 배치 최적화
        const fieldFragment = document.createDocumentFragment();
        
        // 같은 포지션의 선수들끼리 듀오인 경우 - 공간 활용 최적화
        if (samePosition && player1Pos && player2Pos) {
            // 필드 크기 고려하여 적절한 간격으로 배치
            const fieldWidth = 100; // viewBox 기준
            const fieldHeight = 68;
            
            // 중앙 포지션: 상하로 배치 (공간 활용)
            if (player1.position === 'CB' || player1.position === 'CM' || player1.position === 'ST' || 
                player1.position === 'CDM' || player1.position === 'CAM' || player1.position === 'CF') {
                // 상하로 배치 (더 넓은 간격 - 텍스트 겹침 방지)
                const adjustedPos1 = { x: player1Pos.x, y: player1Pos.y - 8 };
                const adjustedPos2 = { x: player2Pos.x, y: player2Pos.y + 8 };
                
                const marker1 = createPlayerMarker(duo.player1_name, adjustedPos1.x, adjustedPos1.y, '#4ECDC4');
                const marker2 = createPlayerMarker(duo.player2_name, adjustedPos2.x, adjustedPos2.y, '#FF6B6B');
                fieldFragment.appendChild(marker1);
                fieldFragment.appendChild(marker2);
                
                // 패스 연결선
                const connection = createPassConnection(adjustedPos1.x, adjustedPos1.y, adjustedPos2.x, adjustedPos2.y, duo.pass_frequency);
                let defs = fieldSVG.querySelector('defs');
                if (!defs) {
                    defs = document.createElementNS('http://www.w3.org/2000/svg', 'defs');
                    fieldSVG.insertBefore(defs, fieldSVG.firstChild);
                }
                if (connection.marker) {
                    defs.appendChild(connection.marker);
                }
                fieldFragment.appendChild(connection.line);
            } else if (player1.position === 'LB' || player1.position === 'RB' || 
                       player1.position === 'LWB' || player1.position === 'RWB' ||
                       player1.position === 'LM' || player1.position === 'RM' ||
                       player1.position === 'LW' || player1.position === 'RW') {
                // 측면 포지션: 좌우로 배치 (측면 공간 활용 - 텍스트 겹침 방지)
                const adjustedPos1 = { x: player1Pos.x - 7, y: player1Pos.y };
                const adjustedPos2 = { x: player2Pos.x + 7, y: player2Pos.y };
                
                const marker1 = createPlayerMarker(duo.player1_name, adjustedPos1.x, adjustedPos1.y, '#4ECDC4');
                const marker2 = createPlayerMarker(duo.player2_name, adjustedPos2.x, adjustedPos2.y, '#FF6B6B');
                fieldFragment.appendChild(marker1);
                fieldFragment.appendChild(marker2);
                
                // 패스 연결선
                const connection = createPassConnection(adjustedPos1.x, adjustedPos1.y, adjustedPos2.x, adjustedPos2.y, duo.pass_frequency);
                let defs = fieldSVG.querySelector('defs');
                if (!defs) {
                    defs = document.createElementNS('http://www.w3.org/2000/svg', 'defs');
                    fieldSVG.insertBefore(defs, fieldSVG.firstChild);
                }
                if (connection.marker) {
                    defs.appendChild(connection.marker);
                }
                fieldFragment.appendChild(connection.line);
            } else {
                // 기타 포지션: 상하로 배치 (텍스트 겹침 방지)
                const adjustedPos1 = { x: player1Pos.x, y: player1Pos.y - 8 };
                const adjustedPos2 = { x: player2Pos.x, y: player2Pos.y + 8 };
                
                const marker1 = createPlayerMarker(duo.player1_name, adjustedPos1.x, adjustedPos1.y, '#4ECDC4');
                const marker2 = createPlayerMarker(duo.player2_name, adjustedPos2.x, adjustedPos2.y, '#FF6B6B');
                fieldFragment.appendChild(marker1);
                fieldFragment.appendChild(marker2);
                
                // 패스 연결선
                const connection = createPassConnection(adjustedPos1.x, adjustedPos1.y, adjustedPos2.x, adjustedPos2.y, duo.pass_frequency);
                let defs = fieldSVG.querySelector('defs');
                if (!defs) {
                    defs = document.createElementNS('http://www.w3.org/2000/svg', 'defs');
                    fieldSVG.insertBefore(defs, fieldSVG.firstChild);
                }
                if (connection.marker) {
                    defs.appendChild(connection.marker);
                }
                fieldFragment.appendChild(connection.line);
            }
        } else {
            // 다른 포지션이거나 위치 정보가 없는 경우 기존 방식
            if (player1Pos) {
                const marker1 = createPlayerMarker(duo.player1_name, player1Pos.x, player1Pos.y, '#4ECDC4');
                fieldFragment.appendChild(marker1);
            }
            if (player2Pos) {
                const marker2 = createPlayerMarker(duo.player2_name, player2Pos.x, player2Pos.y, '#FF6B6B');
                fieldFragment.appendChild(marker2);
            }
            
            // 패스 연결선
            if (player1Pos && player2Pos) {
                const connection = createPassConnection(player1Pos.x, player1Pos.y, player2Pos.x, player2Pos.y, duo.pass_frequency);
                let defs = fieldSVG.querySelector('defs');
                if (!defs) {
                    defs = document.createElementNS('http://www.w3.org/2000/svg', 'defs');
                    fieldSVG.insertBefore(defs, fieldSVG.firstChild);
                }
                if (connection.marker) {
                    defs.appendChild(connection.marker);
                }
                fieldFragment.appendChild(connection.line);
            }
        }
        
        // 한 번에 추가
        fieldSVG.appendChild(fieldFragment);
        
        duoCard.innerHTML = `
            <div class="duo-header">
                <h4>${duo.player1_name} + ${duo.player2_name}</h4>
                <span class="game-count">${duo.games_together}경기</span>
            </div>
            <div class="duo-content">
                <div class="gauge-container">
                    ${winRateGauge}
                </div>
                <div class="field-container">
                    ${fieldSVG.outerHTML}
                </div>
            </div>
        `;
        
        fragment.appendChild(duoCard);
    });
    
    // 한 번에 DOM에 추가 (성능 개선)
    container.appendChild(fragment);
}

// 승률 게이지 차트 생성 (반원형, 가독성 개선, 경기수와 신뢰도 분리)
function createWinRateGauge(winRate, gameCount) {
    const percentage = winRate * 100;
    const radius = 60; // 크기 증가
    const circumference = Math.PI * radius;
    const offset = circumference - (percentage / 100) * circumference;
    
    // 신뢰도 계산 (경기 수에 따라)
    const confidence = Math.min(1, gameCount / 20); // 20경기 이상이면 최대 신뢰도
    const confidenceColor = confidence >= 0.7 ? '#4CAF50' : (confidence >= 0.5 ? '#FF9800' : '#F44336');
    
    // 고유 ID 생성 (여러 게이지가 있을 때 충돌 방지)
    const uniqueId = `gauge-${Math.random().toString(36).substr(2, 9)}`;
    
    return `
        <div class="win-rate-gauge-container">
            <div class="win-rate-gauge">
                <svg width="180" height="100" viewBox="0 0 180 100">
                    <defs>
                        <linearGradient id="${uniqueId}-gradient" x1="0%" y1="0%" x2="100%" y2="0%">
                            <stop offset="0%" style="stop-color:#4CAF50;stop-opacity:1" />
                            <stop offset="50%" style="stop-color:#FFC107;stop-opacity:1" />
                            <stop offset="100%" style="stop-color:#F44336;stop-opacity:1" />
                        </linearGradient>
                    </defs>
                    <!-- 배경 원호 -->
                    <path d="M 30 80 A 60 60 0 0 1 150 80" 
                          fill="none" 
                          stroke="#e0e0e0" 
                          stroke-width="10" 
                          stroke-linecap="round"/>
                    <!-- 승률 원호 -->
                    <path d="M 30 80 A 60 60 0 0 1 150 80" 
                          fill="none" 
                          stroke="url(#${uniqueId}-gradient)" 
                          stroke-width="10" 
                          stroke-linecap="round"
                          stroke-dasharray="${circumference}"
                          stroke-dashoffset="${offset}"
                          transform="rotate(180 90 80)"/>
                    <!-- 텍스트 (크기 증가) -->
                    <text x="90" y="60" text-anchor="middle" fill="#333" font-size="32" font-weight="bold">
                        ${percentage.toFixed(1)}%
                    </text>
                </svg>
            </div>
            <div class="gauge-info">
                <div class="game-count-info">
                    <span class="info-label">경기 수</span>
                    <span class="info-value">${gameCount}경기</span>
                </div>
                <div class="confidence-info">
                    <span class="info-label">신뢰도</span>
                    <span class="info-value" style="color: ${confidenceColor}">
                        ${(confidence * 100).toFixed(0)}%
                    </span>
                </div>
            </div>
        </div>
    `;
}

// 텍스트 바운딩 박스 계산 (대략적 추정)
function calculateTextBounds(text, x, y, fontSize = 2.5) {
    // 한글 기준 대략적인 문자 폭 (fontSize * 0.8)
    const charWidth = fontSize * 0.8;
    const textWidth = text.length * charWidth;
    const textHeight = fontSize * 1.2;
    
    // 텍스트는 마커 위에 표시되므로 (y - 6) 위치
    const textY = y - 6;
    
    return {
        left: x - textWidth / 2,
        right: x + textWidth / 2,
        top: textY - textHeight / 2,
        bottom: textY + textHeight / 2,
        width: textWidth,
        height: textHeight
    };
}

// 마커 바운딩 박스 계산 (원형 마커 + 텍스트 포함)
function calculateMarkerBounds(x, y, text, markerRadius = 3.5, fontSize = 2.5) {
    const textBounds = calculateTextBounds(text, x, y, fontSize);
    const markerTop = y - markerRadius;
    const markerBottom = y + markerRadius;
    const markerLeft = x - markerRadius;
    const markerRight = x + markerRadius;
    
    // 마커와 텍스트를 모두 포함하는 바운딩 박스
    return {
        left: Math.min(textBounds.left, markerLeft),
        right: Math.max(textBounds.right, markerRight),
        top: Math.min(textBounds.top, markerTop),
        bottom: Math.max(textBounds.bottom, markerBottom),
        centerX: x,
        centerY: y
    };
}

// 두 바운딩 박스 간 충돌 감지
function checkCollision(bounds1, bounds2, minPadding = 2) {
    return !(
        bounds1.right + minPadding < bounds2.left ||
        bounds2.right + minPadding < bounds1.left ||
        bounds1.bottom + minPadding < bounds2.top ||
        bounds2.bottom + minPadding < bounds1.top
    );
}

// 노드 위치 조정 (충돌 방지)
function adjustNodePositions(nodes, fieldWidth = 100, fieldHeight = 68) {
    const adjustedNodes = [];
    const minPadding = 3; // 최소 여백
    
    nodes.forEach((node, idx) => {
        let adjustedPos = { x: node.x, y: node.y };
        let attempts = 0;
        const maxAttempts = 50;
        
        // 이전 노드들과 충돌하지 않을 때까지 위치 조정
        while (attempts < maxAttempts) {
            let hasCollision = false;
            const currentBounds = calculateMarkerBounds(adjustedPos.x, adjustedPos.y, node.text);
            
            // 이전에 배치된 노드들과 충돌 확인
            for (let i = 0; i < adjustedNodes.length; i++) {
                const prevBounds = calculateMarkerBounds(
                    adjustedNodes[i].x, 
                    adjustedNodes[i].y, 
                    adjustedNodes[i].text
                );
                
                if (checkCollision(currentBounds, prevBounds, minPadding)) {
                    hasCollision = true;
                    break;
                }
            }
            
            if (!hasCollision) {
                // 필드 경계 내에 있는지 확인
                const bounds = calculateMarkerBounds(adjustedPos.x, adjustedPos.y, node.text);
                if (bounds.left >= 0 && bounds.right <= fieldWidth &&
                    bounds.top >= 0 && bounds.bottom <= fieldHeight) {
                    break;
                }
            }
            
            // 충돌이 있거나 경계를 벗어나면 위치 조정
            // 원형 패턴으로 위치 탐색
            const angle = (attempts * 0.5) % (Math.PI * 2);
            const radius = 2 + (attempts * 0.3);
            adjustedPos = {
                x: node.x + Math.cos(angle) * radius,
                y: node.y + Math.sin(angle) * radius
            };
            
            attempts++;
        }
        
        adjustedNodes.push({
            x: adjustedPos.x,
            y: adjustedPos.y,
            text: node.text,
            color: node.color,
            players: node.players
        });
    });
    
    return adjustedNodes;
}

// 선수 마커 생성 (선수 이름 표시 개선, 줄바꿈 지원)
function createPlayerMarker(playerName, x, y, color) {
    const g = document.createElementNS('http://www.w3.org/2000/svg', 'g');
    g.setAttribute('transform', `translate(${x}, ${y})`);
    
    // SVG의 viewBox scaleFactor를 확인하여 마커 및 텍스트 크기 조정
    const svgElement = g.ownerDocument?.documentElement || g.closest('svg');
    let scaleFactor = 1.0;
    if (svgElement) {
        const viewBox = svgElement.getAttribute('viewBox');
        if (viewBox) {
            const [, , vw, vh] = viewBox.split(' ').map(Number);
            if (vw && vw > 100) {
                scaleFactor = vw / 100; // viewBox가 확대되었으면 scaleFactor 계산
            }
        }
    }
    
    // 원형 마커 (크기 증가, scaleFactor 적용하여 절대 크기 유지)
    const circle = document.createElementNS('http://www.w3.org/2000/svg', 'circle');
    circle.setAttribute('r', 3.5 * scaleFactor);
    circle.setAttribute('fill', color);
    circle.setAttribute('stroke', '#fff');
    circle.setAttribute('stroke-width', 0.5 * scaleFactor);
    circle.setAttribute('class', 'player-marker');
    g.appendChild(circle);
    
    // 선수 이름 텍스트 (줄바꿈 지원)
    
    const lines = playerName.split('\n');
    const lineHeight = 3 * scaleFactor; // scaleFactor 적용
    const startY = -6 * scaleFactor - ((lines.length - 1) * lineHeight / 2);
    const fontSize = 2.5 * scaleFactor; // 폰트 크기도 scaleFactor 적용하여 절대 크기 유지
    
    lines.forEach((line, idx) => {
        const text = document.createElementNS('http://www.w3.org/2000/svg', 'text');
        text.setAttribute('x', '0');
        text.setAttribute('y', startY + (idx * lineHeight));
        text.setAttribute('text-anchor', 'middle');
        text.setAttribute('font-size', fontSize);
        text.setAttribute('font-weight', 'bold');
        text.setAttribute('fill', '#fff');
        text.setAttribute('stroke', '#000');
        text.setAttribute('stroke-width', 0.2 * scaleFactor);
        text.setAttribute('paint-order', 'stroke fill');
        text.textContent = line;
        g.appendChild(text);
    });
    
    // 선수 이름 (호버 시 상세 표시)
    const title = document.createElementNS('http://www.w3.org/2000/svg', 'title');
    title.textContent = playerName.replace(/\n/g, ', ');
    g.appendChild(title);
    
    return g;
}

// 패스 연결선 생성
function createPassConnection(x1, y1, x2, y2, frequency) {
    const line = document.createElementNS('http://www.w3.org/2000/svg', 'line');
    line.setAttribute('x1', x1);
    line.setAttribute('y1', y1);
    line.setAttribute('x2', x2);
    line.setAttribute('y2', y2);
    
    // 빈도에 따라 선 두께 조정
    const strokeWidth = Math.min(1.5, 0.3 + (frequency / 100) * 1.2);
    line.setAttribute('stroke', '#FFD700');
    line.setAttribute('stroke-width', strokeWidth);
    line.setAttribute('opacity', '0.6');
    line.setAttribute('stroke-dasharray', '1,1');
    line.setAttribute('class', 'pass-connection');
    
    // 화살표 마커
    const arrow = document.createElementNS('http://www.w3.org/2000/svg', 'marker');
    const uniqueId = `arrow-${Math.random().toString(36).substr(2, 9)}`;
    arrow.setAttribute('id', uniqueId);
    arrow.setAttribute('markerWidth', '4');
    arrow.setAttribute('markerHeight', '4');
    arrow.setAttribute('refX', '3');
    arrow.setAttribute('refY', '2');
    arrow.setAttribute('orient', 'auto');
    
    const path = document.createElementNS('http://www.w3.org/2000/svg', 'path');
    path.setAttribute('d', 'M0,0 L0,4 L4,2 z');
    path.setAttribute('fill', '#FFD700');
    arrow.appendChild(path);
    
    line.setAttribute('marker-end', `url(#${uniqueId})`);
    
    return { line, marker: arrow };
}

// 선수 포지션 찾기 (팀 데이터에서)
function findPlayerPosition(playerId, teamData) {
    if (!teamData || !teamData.players) return null;
    
    const player = teamData.players.find(p => p.player_id === playerId);
    if (!player || !player.position) return null;
    
    // 포지션별 기본 좌표 (4-3-3 기준)
    const positionMap = {
        'GK': { x: 5, y: 34 },
        'CB': { x: 15, y: 34 },
        'LB': { x: 15, y: 15 },
        'RB': { x: 15, y: 53 },
        'CDM': { x: 30, y: 34 },
        'CM': { x: 35, y: 34 },
        'CAM': { x: 50, y: 34 },
        'LM': { x: 35, y: 15 },
        'RM': { x: 35, y: 53 },
        'LW': { x: 65, y: 15 },
        'RW': { x: 65, y: 53 },
        'ST': { x: 80, y: 34 },
        'CF': { x: 75, y: 34 }
    };
    
    return positionMap[player.position] || { x: 50, y: 34 };
}

// 클러스터 효과성 인포그래픽 생성 (최적화)
function createClusterEffectivenessInfographic(container, clusters, teamData) {
    container.innerHTML = '';
    
    // 최소 경기 수 필터링 (10경기 이상)
    const significantClusters = clusters.filter(c => c.active_games >= 10);
    
    if (significantClusters.length === 0) {
        container.innerHTML = '<div class="insufficient-data"><p>통계적 유의성을 위한 충분한 데이터가 없습니다.<br>최소 10경기 이상 활성화된 클러스터만 표시됩니다.</p></div>';
        return;
    }
    
    const topClusters = significantClusters.slice(0, 3);
    
    // DocumentFragment 사용 (성능 개선)
    const fragment = document.createDocumentFragment();
    
    topClusters.forEach((cluster, idx) => {
        const clusterCard = document.createElement('div');
        clusterCard.className = 'cluster-infographic-card';
        
        // 승률 게이지
        const winRateGauge = createWinRateGauge(cluster.win_rate, cluster.active_games);
        
        // 필드 다이어그램 (크기 확대, scaleFactor 2.0으로 폰트 크기 유지)
        const fieldSVG = createFootballFieldSVG(800, 560, 2.0);
        
        // DocumentFragment로 배치 최적화
        const fieldFragment = document.createDocumentFragment();
        
        // 선수 위치 캐싱 및 마커 생성 (같은 위치의 선수들을 그룹화)
        const playerPositions = new Map(); // playerId -> position (연결선용)
        const playerNames = cluster.player_names || [];
        
        // 좌표별로 선수 그룹화 (같은 위치의 선수들을 하나로 묶기)
        const playersByLocation = new Map(); // "x-y" -> { pos: {x, y}, players: [{id, name}] }
        
        // cluster.players 배열과 player_names 배열을 매칭
        cluster.players.forEach((playerId, playerIdx) => {
            const player = teamData.players.find(p => p.player_id === playerId);
            const playerName = player ? (player.player_name || playerNames[playerIdx] || `선수${playerIdx + 1}`) : (playerNames[playerIdx] || `선수${playerIdx + 1}`);
            
            if (player || playerNames[playerIdx]) {
                const pos = findPlayerPosition(playerId, teamData);
                if (pos) {
                    // 좌표를 반올림하여 근접한 위치를 같은 그룹으로 처리 (0.5 단위)
                    const roundedX = Math.round(pos.x * 2) / 2;
                    const roundedY = Math.round(pos.y * 2) / 2;
                    const locationKey = `${roundedX}-${roundedY}`;
                    
                    playerPositions.set(playerId, pos);
                    
                    // 같은 위치의 선수들을 그룹화
                    if (!playersByLocation.has(locationKey)) {
                        playersByLocation.set(locationKey, {
                            pos: { x: roundedX, y: roundedY },
                            players: []
                        });
                    }
                    playersByLocation.get(locationKey).players.push({
                        id: playerId,
                        name: playerName
                    });
                }
            }
        });
        
        // player_names에만 있고 players 배열에 없는 경우도 처리
        if (playerNames && playerNames.length > cluster.players.length) {
            playerNames.forEach((playerName, nameIdx) => {
                if (nameIdx >= cluster.players.length) {
                    // 새로운 선수 위치 찾기 (기본 위치 사용)
                    const defaultPos = { x: 50 + (nameIdx % 3) * 10, y: 20 + Math.floor(nameIdx / 3) * 15 };
                    const roundedX = Math.round(defaultPos.x * 2) / 2;
                    const roundedY = Math.round(defaultPos.y * 2) / 2;
                    const locationKey = `${roundedX}-${roundedY}`;
                    
                    if (!playersByLocation.has(locationKey)) {
                        playersByLocation.set(locationKey, {
                            pos: { x: roundedX, y: roundedY },
                            players: []
                        });
                    }
                    playersByLocation.get(locationKey).players.push({
                        id: null,
                        name: playerName
                    });
                }
            });
        }
        
        // 그룹화된 선수들을 마커로 생성 (원래 위치 유지, 텍스트 줄바꿈 처리)
        playersByLocation.forEach((group, locationKey) => {
            let text, hue, color;
            if (group.players.length === 1) {
                // 단일 선수
                const player = group.players[0];
                text = player.name;
                hue = (player.id || 0) % 360;
            } else {
                // 같은 위치의 여러 선수 - 콤마로 구분 (줄바꿈 처리)
                const names = group.players.map(p => p.name);
                // 긴 텍스트는 줄바꿈 (예: 3명 이상이거나 총 길이가 15자 이상)
                if (names.length > 2 || names.join(', ').length > 15) {
                    // 2명씩 줄바꿈
                    const lines = [];
                    for (let i = 0; i < names.length; i += 2) {
                        lines.push(names.slice(i, i + 2).join(', '));
                    }
                    text = lines.join('\n');
                } else {
                    text = names.join(', ');
                }
                hue = (group.players[0].id || 0) % 360;
            }
            color = `hsl(${hue}, 70%, 50%)`;
            
            const marker = createPlayerMarker(text, group.pos.x, group.pos.y, color);
            fieldFragment.appendChild(marker);
        });
        
        // 클러스터 연결선 (선수 간 패스) - 조정된 위치 사용
        let defs = fieldSVG.querySelector('defs');
        if (!defs) {
            defs = document.createElementNS('http://www.w3.org/2000/svg', 'defs');
            fieldSVG.insertBefore(defs, fieldSVG.firstChild);
        }
        
        // 연결선 생성 (최대 10개만 표시하여 성능 개선)
        const connections = [];
        const playerIds = Array.from(playerPositions.keys());
        for (let i = 0; i < playerIds.length && connections.length < 10; i++) {
            for (let j = i + 1; j < playerIds.length && connections.length < 10; j++) {
                const pos1 = playerPositions.get(playerIds[i]);
                const pos2 = playerPositions.get(playerIds[j]);
                
                if (pos1 && pos2) {
                    const connection = createPassConnection(pos1.x, pos1.y, pos2.x, pos2.y, cluster.cohesion / 10);
                    connections.push(connection);
                }
            }
        }
        
        // 마커 추가 및 연결선 추가
        connections.forEach((connection, markerIdx) => {
            if (connection.marker) {
                const uniqueId = `arrow-cluster-${idx}-${markerIdx}`;
                connection.marker.setAttribute('id', uniqueId);
                connection.line.setAttribute('marker-end', `url(#${uniqueId})`);
                defs.appendChild(connection.marker);
            }
            fieldFragment.appendChild(connection.line);
        });
        
        // 한 번에 추가
        fieldSVG.appendChild(fieldFragment);
        
        clusterCard.innerHTML = `
            <div class="cluster-header">
                <h4>클러스터 ${idx + 1}</h4>
                <span class="cluster-size">${cluster.cluster_size}명</span>
            </div>
            <div class="cluster-content">
                <div class="gauge-container">
                    ${winRateGauge}
                </div>
                <div class="field-container">
                    ${fieldSVG.outerHTML}
                </div>
            </div>
        `;
        
        fragment.appendChild(clusterCard);
    });
    
    // 한 번에 DOM에 추가 (성능 개선)
    container.appendChild(fragment);
}


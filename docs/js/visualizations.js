// 시각화 관련 함수들

let radarChart = null;
let passNetworkChart = null;

// 비교할 선수 목록 (전역)
let selectedComparisonPlayers = [];

// HEX 색상을 RGB 문자열로 변환하는 함수
function hexToRgb(hex) {
    const result = /^#?([a-f\d]{2})([a-f\d]{2})([a-f\d]{2})$/i.exec(hex);
    if (result) {
        const r = parseInt(result[1], 16);
        const g = parseInt(result[2], 16);
        const b = parseInt(result[3], 16);
        return `rgb(${r}, ${g}, ${b})`;
    }
    return 'rgb(102, 126, 234)'; // 기본값
}

// 레이더 차트 생성
function createRadarChart(player, comparisonPlayers = []) {
    const canvas = document.getElementById('radar-chart');
    if (!canvas) return;
    
    const ctx = canvas.getContext('2d');
    
    // 기존 차트 제거
    if (radarChart) {
        radarChart.destroy();
    }
    
    if (!player.enhanced || !player.enhanced.detailed_profile) {
        canvas.parentElement.innerHTML = '<p>상세 프로파일 데이터가 없습니다.</p>';
        return;
    }
    
    const profile = player.enhanced.detailed_profile;
    
    // 레이더 차트용 지표 선택
    const metrics = [
        'pass_success_rate',
        'long_pass_ratio',
        'forward_pass_ratio',
        'average_pass_length',
        'touch_zone_central',
        'touch_zone_forward',
        'defensive_action_frequency',
        'carry_frequency'
    ];
    
    const metricLabels = {
        'pass_success_rate': '패스 성공률',
        'long_pass_ratio': '롱패스 비율',
        'forward_pass_ratio': '전진 패스 비율',
        'average_pass_length': '평균 패스 거리',
        'touch_zone_central': '중앙 지역 터치',
        'touch_zone_forward': '전방 지역 터치',
        'defensive_action_frequency': '수비 행동 빈도',
        'carry_frequency': '캐리 빈도'
    };
    
    // 데이터 정규화 (0-100 범위)
    const datasets = [];
    
    // 현재 선수 데이터
    const playerData = metrics.map(m => {
        const value = profile[m] || 0;
        // 정규화 (각 지표의 최대값 기준)
        return Math.min(100, value * 100);
    });
    
    // 현재 선수의 팀 색상 가져오기
    const currentTeamColor = getTeamColor(currentTeam ? currentTeam.team_name : '');
    const currentTeamPrimaryRgb = hexToRgb(currentTeamColor.primary);
    // RGB 문자열에서 숫자 추출
    const rgbMatch = currentTeamPrimaryRgb.match(/rgb\((\d+),\s*(\d+),\s*(\d+)\)/);
    const currentTeamPrimary = rgbMatch ? {
        r: parseInt(rgbMatch[1]),
        g: parseInt(rgbMatch[2]),
        b: parseInt(rgbMatch[3])
    } : { r: 102, g: 126, b: 234 };
    
    datasets.push({
        label: player.player_name,
        data: playerData,
        borderColor: currentTeamPrimaryRgb,
        backgroundColor: `rgba(${currentTeamPrimary.r}, ${currentTeamPrimary.g}, ${currentTeamPrimary.b}, 0.2)`,
        borderWidth: 3
    });
    
    // 비교 선수 데이터 (선택된 선수들)
    const playersToCompare = comparisonPlayers.length > 0 ? comparisonPlayers : selectedComparisonPlayers;
    
    if (playersToCompare && playersToCompare.length > 0) {
        playersToCompare.forEach((compPlayer, idx) => {
            let profile = null;
            if (compPlayer.profile) {
                profile = compPlayer.profile;
            } else if (compPlayer.enhanced && compPlayer.enhanced.detailed_profile) {
                profile = compPlayer.enhanced.detailed_profile;
            }
            
            if (profile) {
                const compData = metrics.map(m => {
                    const value = profile[m] || 0;
                    return Math.min(100, value * 100);
                });
                
                // 비교 선수의 팀 색상 가져오기
                const compTeamName = compPlayer.team_name || '';
                const compTeamColor = getTeamColor(compTeamName);
                const compTeamPrimaryRgb = hexToRgb(compTeamColor.primary);
                // RGB 문자열에서 숫자 추출
                const compRgbMatch = compTeamPrimaryRgb.match(/rgb\((\d+),\s*(\d+),\s*(\d+)\)/);
                const compTeamPrimary = compRgbMatch ? {
                    r: parseInt(compRgbMatch[1]),
                    g: parseInt(compRgbMatch[2]),
                    b: parseInt(compRgbMatch[3])
                } : { r: 102, g: 126, b: 234 };
                
                datasets.push({
                    label: `${compPlayer.player_name || compPlayer.name} (${compTeamName})`,
                    data: compData,
                    borderColor: compTeamPrimaryRgb,
                    backgroundColor: `rgba(${compTeamPrimary.r}, ${compTeamPrimary.g}, ${compTeamPrimary.b}, 0.2)`,
                    borderWidth: 2
                });
            }
        });
    }
    
    // 캔버스 크기 설정 (중앙 정렬을 위해)
    const chartSize = Math.min(400, window.innerWidth * 0.8);
    canvas.width = chartSize;
    canvas.height = chartSize;
    
    radarChart = new Chart(ctx, {
        type: 'radar',
        data: {
            labels: metrics.map(m => metricLabels[m] || m),
            datasets: datasets
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            layout: {
                padding: 20
            },
            scales: {
                r: {
                    beginAtZero: true,
                    max: 100,
                    ticks: {
                        stepSize: 20
                    },
                    pointLabels: {
                        font: {
                            size: 12
                        }
                    }
                }
            },
            plugins: {
                legend: {
                    position: 'top',
                },
                title: {
                    display: true,
                    text: '선수 능력치 비교'
                }
            }
        }
    });
}

// 패스 네트워크 시각화 (D3.js 그래프)
function createPassNetwork(player) {
    const container = document.getElementById('pass-network');
    if (!container) return;
    
    // 전역 변수에서 currentTeam 사용
    const teamForNetwork = currentTeam;
    
    if (!player.enhanced || !player.enhanced.pass_network) {
        container.innerHTML = '<p>패스 네트워크 데이터가 없습니다.</p>';
        return;
    }
    
    const network = player.enhanced.pass_network;
    const topConnections = network.top_connections || [];
    
    if (topConnections.length === 0) {
        container.innerHTML = '<p>주요 패스 연결이 없습니다.</p>';
        return;
    }
    
    // 기존 시각화 제거
    container.innerHTML = '';
    d3.select('#pass-network').selectAll('*').remove();
    
    // 포지션별 색상 매핑
    const positionColors = {
        'GK': '#FF6B6B',
        'CB': '#4ECDC4',
        'LB': '#45B7D1',
        'RB': '#45B7D1',
        'LWB': '#96CEB4',
        'RWB': '#96CEB4',
        'CDM': '#FFEAA7',
        'CM': '#FDCB6E',
        'CAM': '#E17055',
        'LM': '#A29BFE',
        'RM': '#A29BFE',
        'LW': '#FD79A8',
        'RW': '#FD79A8',
        'CF': '#FF7675',
        'ST': '#FF7675'
    };
    
    // 포지션 한글명 매핑
    const positionLabels = {
        'GK': '골키퍼',
        'CB': '센터백',
        'LB': '왼쪽 풀백',
        'RB': '오른쪽 풀백',
        'LWB': '왼쪽 윙백',
        'RWB': '오른쪽 윙백',
        'CDM': '수비형 미드필더',
        'CM': '중앙 미드필더',
        'CAM': '공격형 미드필더',
        'LM': '왼쪽 미드필더',
        'RM': '오른쪽 미드필더',
        'LW': '왼쪽 윙어',
        'RW': '오른쪽 윙어',
        'CF': '공격수',
        'ST': '스트라이커'
    };
    
    // SVG 컨테이너 생성 (범례 공간 확보)
    const legendWidth = 280; // 범례 너비 증가 (2열을 위해)
    const graphWidth = Math.min(800, container.clientWidth || 800);
    const totalWidth = graphWidth + legendWidth + 40; // 그래프 + 범례 + 여백
    const height = 600;
    
    const svg = d3.select('#pass-network')
        .append('svg')
        .attr('id', 'pass-network-visualization')
        .attr('width', totalWidth)
        .attr('height', height)
        .style('border', '1px solid #e0e0e0')
        .style('border-radius', '8px');
    
    // 노드와 엣지 데이터 준비
    const nodes = [];
    const links = [];
    
    // 현재 선수를 중심 노드로 추가
    const totalPassCount = topConnections.reduce((sum, conn) => sum + conn.count, 0);
    nodes.push({
        id: player.player_id,
        name: player.player_name,
        type: 'center',
        position: player.position,
        size: 25,
        pass_count: totalPassCount
    });
    
    // 연결된 선수들을 노드로 추가 (포지션 정보 포함)
    topConnections.forEach(conn => {
        if (!nodes.find(n => n.id === conn.receiver_id)) {
            // 수신자 선수의 포지션 찾기
            let receiverPosition = 'Unknown';
            if (teamForNetwork && teamForNetwork.players) {
                const receiverPlayer = teamForNetwork.players.find(p => p.player_id === conn.receiver_id);
                if (receiverPlayer) {
                    receiverPosition = receiverPlayer.position;
                }
            }
            
            nodes.push({
                id: conn.receiver_id,
                name: conn.receiver_name,
                type: 'receiver',
                position: receiverPosition,
                size: 15 + Math.sqrt(conn.count) * 2, // 패스 빈도에 따라 크기 조정
                pass_count: conn.count
            });
        }
        
        // 엣지 추가
        links.push({
            source: player.player_id,
            target: conn.receiver_id,
            value: conn.count,
            success_rate: conn.success_rate
        });
    });
    
    // Force simulation 설정 (범례 영역 제외)
    const graphCenterX = graphWidth / 2;
    const graphCenterY = height / 2;
    
    // 노드가 범례 영역으로 가지 않도록 제한
    const minX = 10;
    const maxX = graphWidth - 10;
    const minY = 10;
    const maxY = height - 10;
    
    const simulation = d3.forceSimulation(nodes)
        .force('link', d3.forceLink(links).id(d => d.id).distance(150))
        .force('charge', d3.forceManyBody().strength(-300))
        .force('center', d3.forceCenter(graphCenterX, graphCenterY))
        .force('collision', d3.forceCollide().radius(d => d.size + 10))
        .force('x', d3.forceX(graphCenterX).strength(0.2))
        .force('y', d3.forceY(graphCenterY).strength(0.2))
        .on('tick', () => {
            // 노드 위치 제한 (범례 영역 제외)
            nodes.forEach(d => {
                d.x = Math.max(minX, Math.min(maxX, d.x));
                d.y = Math.max(minY, Math.min(maxY, d.y));
            });
        });
    
    // 엣지 그리기
    const link = svg.append('g')
        .selectAll('line')
        .data(links)
        .enter()
        .append('line')
        .attr('stroke', '#999')
        .attr('stroke-opacity', 0.6)
        .attr('stroke-width', d => Math.sqrt(d.value) * 0.5)
        .attr('marker-end', 'url(#arrowhead)');
    
    // 화살표 마커 정의
    svg.append('defs').append('marker')
        .attr('id', 'arrowhead')
        .attr('viewBox', '0 -5 10 10')
        .attr('refX', 25)
        .attr('refY', 0)
        .attr('markerWidth', 6)
        .attr('markerHeight', 6)
        .attr('orient', 'auto')
        .append('path')
        .attr('d', 'M0,-5L10,0L0,5')
        .attr('fill', '#999');
    
    // 노드 그리기
    const node = svg.append('g')
        .selectAll('g')
        .data(nodes)
        .enter()
        .append('g')
        .call(d3.drag()
            .on('start', dragstarted)
            .on('drag', dragged)
            .on('end', dragended));
    
    // 노드 원 (포지션별 색상)
    const circles = node.append('circle')
        .attr('r', d => d.size)
        .attr('fill', d => {
            if (d.type === 'center') {
                return '#667eea'; // 현재 선수는 파란색
            }
            return positionColors[d.position] || '#764ba2'; // 포지션별 색상
        })
        .attr('stroke', '#fff')
        .attr('stroke-width', d => d.type === 'center' ? 3 : 2)
        .attr('class', 'network-node')
        .style('cursor', d => d.type === 'center' ? 'default' : 'pointer')
        .on('click', function(event, d) {
            event.stopPropagation();
            if (d.type !== 'center' && d.id) {
                // 수신자 선수 상세 페이지로 이동
                if (typeof window.selectPlayer === 'function') {
                    window.selectPlayer(d.id);
                }
            }
        });
    
    // 노드 툴팁 (포지션 정보 포함)
    circles.append('title')
        .text(d => {
            const name = d.name || '알 수 없음';
            const position = d.position || 'Unknown';
            const passCount = d.pass_count || 0;
            const clickHint = d.type === 'center' ? '' : '\n클릭하여 상세 정보 보기';
            return `${name} (${position})\n패스: ${passCount}회${clickHint}`;
        });
    
    // 패스 빈도 표시 (노드 내부)
    node.append('text')
        .attr('class', 'pass-count-badge')
        .text(d => {
            const count = d.pass_count || 0;
            return count > 0 ? count : '';
        })
        .attr('font-size', d => d.type === 'center' ? '11px' : '9px')
        .attr('font-weight', 'bold');
    
    // 노드 레이블
    node.append('text')
        .attr('class', 'network-node-label')
        .text(d => {
            const name = d.name || '';
            return name.length > 8 ? name.substring(0, 6) + '...' : name;
        })
        .attr('dx', d => d.size + 5)
        .attr('dy', 4)
        .attr('font-size', '11px')
        .attr('fill', '#333')
        .attr('font-weight', d => d.type === 'center' ? 'bold' : 'normal');
    
    // 툴팁
    const tooltip = d3.select('body').append('div')
        .attr('class', 'network-tooltip')
        .style('opacity', 0)
        .style('position', 'absolute')
        .style('background', 'rgba(0, 0, 0, 0.8)')
        .style('color', 'white')
        .style('padding', '8px')
        .style('border-radius', '4px')
        .style('font-size', '12px')
        .style('pointer-events', 'none');
    
    // 엣지 툴팁
    link.append('title')
        .text(d => {
            const sourceName = d.source.name || '알 수 없음';
            const targetName = d.target.name || '알 수 없음';
            return `${sourceName} → ${targetName}\n${d.value}회 (성공률: ${(d.success_rate * 100).toFixed(1)}%)`;
        });
    
    // 노드 툴팁 (포지션 정보 포함)
    node.selectAll('circle').append('title')
        .text(d => {
            const name = d.name || '알 수 없음';
            const position = d.position || 'Unknown';
            const passCount = d.pass_count || 0;
            return `${name} (${position})\n패스: ${passCount}회`;
        });
    
    // 시뮬레이션 업데이트 (tick 이벤트는 이미 위에서 정의됨 - 위치 제한 포함)
    simulation.on('tick', () => {
        link
            .attr('x1', d => d.source.x)
            .attr('y1', d => d.source.y)
            .attr('x2', d => d.target.x)
            .attr('y2', d => d.target.y);
        
        node.attr('transform', d => `translate(${d.x},${d.y})`);
    });
    
    // 드래그 함수
    function dragstarted(event, d) {
        if (!event.active) simulation.alphaTarget(0.3).restart();
        d.fx = d.x;
        d.fy = d.y;
    }
    
    function dragged(event, d) {
        d.fx = event.x;
        d.fy = event.y;
    }
    
    function dragended(event, d) {
        if (!event.active) simulation.alphaTarget(0);
        d.fx = null;
        d.fy = null;
    }
    
    // 범례 생성 (전체 너비 전달)
    createPassNetworkLegend(svg, positionColors, positionLabels, totalWidth, height);
}

// 패스 네트워크 범례 생성
function createPassNetworkLegend(svg, positionColors, positionLabels, totalWidth, height) {
    const legendWidth = 240; // 범례 너비 증가
    const legendHeight = 480; // 범례 높이 증가 (겹침 방지)
    const graphWidth = totalWidth - legendWidth - 40; // 그래프 영역 너비
    const legendX = graphWidth + 20; // 그래프 오른쪽에 20px 여백
    const legendY = 20;
    
    // 기존 범례 제거
    svg.selectAll('.network-legend').remove();
    
    // 범례 배경
    const legendBg = svg.append('g')
        .attr('class', 'network-legend')
        .attr('transform', `translate(${legendX}, ${legendY})`);
    
    legendBg.append('rect')
        .attr('width', legendWidth)
        .attr('height', legendHeight)
        .attr('fill', 'white')
        .attr('stroke', '#ddd')
        .attr('stroke-width', 2)
        .attr('rx', 8)
        .attr('opacity', 0.95);
    
    // 범례 제목
    legendBg.append('text')
        .attr('x', legendWidth / 2)
        .attr('y', 25)
        .attr('text-anchor', 'middle')
        .attr('font-size', '16px')
        .attr('font-weight', 'bold')
        .text('범례');
    
    // 포지션별 색상 범례
    let yPos = 55;
    legendBg.append('text')
        .attr('x', 10)
        .attr('y', yPos)
        .attr('font-size', '12px')
        .attr('font-weight', 'bold')
        .text('포지션별 색상');
    
    yPos += 20;
    const positions = Object.keys(positionColors).filter(pos => positionLabels[pos]);
    positions.forEach((pos, idx) => {
        if (yPos + idx * 20 > legendHeight - 100) return; // 범례 영역 초과 방지
        
        const legendItem = legendBg.append('g')
            .attr('transform', `translate(10, ${yPos + idx * 20})`);
        
        legendItem.append('circle')
            .attr('r', 8)
            .attr('cx', 8)
            .attr('cy', 0)
            .attr('fill', positionColors[pos])
            .attr('stroke', '#fff')
            .attr('stroke-width', 1);
        
        legendItem.append('text')
            .attr('x', 22)
            .attr('y', 4)
            .attr('font-size', '11px')
            .text(positionLabels[pos] || pos);
    });
    
    // 패스 빈도 범례 (엣지 두께) - 위치 조정
    yPos = legendHeight - 180; // 노드 크기 범례와 충분한 여백 확보
    legendBg.append('text')
        .attr('x', 10)
        .attr('y', yPos)
        .attr('font-size', '12px')
        .attr('font-weight', 'bold')
        .text('패스 빈도 (엣지 두께)');
    
    yPos += 20;
    const passFrequencies = [
        { count: 100, label: '100회 이상' },
        { count: 50, label: '50-100회' },
        { count: 20, label: '20-50회' },
        { count: 10, label: '10-20회' }
    ];
    
    passFrequencies.forEach((freq, idx) => {
        const lineY = yPos + idx * 25;
        const lineWidth = Math.sqrt(freq.count) * 0.5;
        
        legendBg.append('line')
            .attr('x1', 10)
            .attr('x2', 60)
            .attr('y1', lineY)
            .attr('y2', lineY)
            .attr('stroke', '#999')
            .attr('stroke-width', lineWidth)
            .attr('opacity', 0.6);
        
        legendBg.append('text')
            .attr('x', 65)
            .attr('y', lineY + 4)
            .attr('font-size', '10px')
            .text(freq.label);
    });
    
    // 노드 크기 범례 (패스 빈도에 따라 크기 변화) - 위치 조정
    yPos = legendHeight - 80; // 하단 여백 확보
    legendBg.append('text')
        .attr('x', 10)
        .attr('y', yPos - 5)
        .attr('font-size', '12px')
        .attr('font-weight', 'bold')
        .attr('fill', '#666')
        .text('노드 크기 = 패스 빈도');
    
    // 노드 크기 예시 (간격 확대)
    const nodeSizes = [
        { size: 20, label: '높음' },
        { size: 15, label: '중간' },
        { size: 10, label: '낮음' }
    ];
    
    yPos += 15;
    nodeSizes.forEach((node, idx) => {
        const circleY = yPos + idx * 30; // 간격을 20에서 30으로 증가
        legendBg.append('circle')
            .attr('cx', 15)
            .attr('cy', circleY)
            .attr('r', node.size)
            .attr('fill', '#4ECDC4')
            .attr('stroke', '#fff')
            .attr('stroke-width', 1);
        
        legendBg.append('text')
            .attr('x', 35)
            .attr('y', circleY + 4)
            .attr('font-size', '10px')
            .text(node.label);
    });
}

// 전역 함수로 노출
window.openInfoModal = function(title, content) {
    const modal = document.getElementById('info-modal');
    const modalBody = document.getElementById('modal-body');
    
    document.getElementById('info-modal').querySelector('h2').textContent = title;
    modalBody.innerHTML = content;
    modal.style.display = 'block';
};

// 모달 닫기
function closeInfoModal() {
    document.getElementById('info-modal').style.display = 'none';
}

// 모달 이벤트 리스너
document.addEventListener('DOMContentLoaded', () => {
    const modal = document.getElementById('info-modal');
    const closeBtn = modal.querySelector('.close');
    
    if (closeBtn) {
        closeBtn.onclick = closeInfoModal;
    }
    
    window.onclick = (event) => {
        if (event.target === modal) {
            closeInfoModal();
        }
    };
});

// 전역 함수로 노출
window.getImplementationInfo = function(type) {
    const info = {
        'radar': `
            <h3>레이더 차트 구현 과정</h3>
            <ol>
                <li><strong>데이터 수집</strong>: 선수의 주요 지표를 계산합니다.
                    <ul>
                        <li>패스 성공률, 롱패스 비율, 전진 패스 비율</li>
                        <li>평균 패스 거리, 터치 위치, 수비 행동 빈도 등</li>
                    </ul>
                </li>
                <li><strong>데이터 정규화</strong>: 각 지표를 0-100 범위로 정규화합니다.</li>
                <li><strong>Chart.js 라이브러리 사용</strong>: Chart.js의 radar 차트 타입을 사용하여 시각화합니다.</li>
                <li><strong>비교 기능</strong>: 같은 포지션/롤의 상위 선수들과 비교할 수 있습니다.</li>
            </ol>
            <p><strong>기술 스택</strong>: Chart.js 4.4.0, JavaScript</p>
        `,
        'pass-network': `
            <h3>패스 네트워크 시각화 구현 과정</h3>
            <ol>
                <li><strong>패스 데이터 추출</strong>: 선수가 패스를 보낸 모든 이벤트를 추출합니다.</li>
                <li><strong>패스 수신자 식별</strong>: 다음 이벤트가 'Pass Received'인 경우를 찾아 수신자를 식별합니다.</li>
                <li><strong>연결 통계 계산</strong>: 각 수신자별 패스 빈도와 성공률을 계산합니다.</li>
                <li><strong>상위 연결 추출</strong>: 가장 빈번한 패스 연결을 식별합니다.</li>
                <li><strong>시각화</strong>: 리스트 형태로 주요 패스 연결을 표시합니다.</li>
            </ol>
            <p><strong>향후 개선</strong>: D3.js를 사용한 네트워크 그래프 시각화 예정</p>
        `,
        'role-fit': `
            <h3>롤 적합도 점수 계산 방법</h3>
            <ol>
                <li><strong>롤 템플릿 정의</strong>: 데이터 기반 클러스터링으로 각 포지션의 롤을 정의합니다.</li>
                <li><strong>선수 프로파일 계산</strong>: 선수의 행동 패턴을 수치화합니다.</li>
                <li><strong>코사인 유사도 (60%)</strong>: 선수와 롤 템플릿의 방향 유사성을 측정합니다.
                    <ul>
                        <li>방향 유사성 측정: 선수의 행동 패턴이 롤 템플릿과 얼마나 같은 방향인지</li>
                    </ul>
                </li>
                <li><strong>유클리드 거리 (40%)</strong>: 선수와 롤 템플릿의 크기 차이를 측정합니다.
                    <ul>
                        <li>크기 차이 측정: 각 지표의 절대적 차이를 계산</li>
                    </ul>
                </li>
                <li><strong>표본 크기 보정</strong>: 베이지안 평균 방식으로 적은 경기 수의 영향을 보정합니다.
                    <ul>
                        <li>신뢰도 계산: 경기 수와 이벤트 수를 기반으로 신뢰도 가중치 계산</li>
                        <li>베이지안 평균: 신뢰도 × 원점수 + (1 - 신뢰도) × 50 (중간값)</li>
                    </ul>
                </li>
                <li><strong>보너스 적용</strong>: 경기 수와 팀 승률에 따른 보너스/페널티를 적용합니다.
                    <ul>
                        <li>경기 수 보너스: 
                            <ul>
                                <li>15경기 이상: +0.5점</li>
                                <li>20경기 이상: +1.0점</li>
                                <li>25경기 이상: +2.0점</li>
                                <li>30경기 이상: +3.0점</li>
                            </ul>
                        </li>
                        <li>팀 승률 기여도: 해당 선수가 뛴 경기에서의 팀 승률에 따른 보너스/페널티
                            <ul>
                                <li>승률 60% 이상: +1.0점</li>
                                <li>승률 50% 이상: +0.5점</li>
                                <li>승률 40% 미만: -0.5점</li>
                                <li>승률 30% 미만: -1.0점</li>
                            </ul>
                        </li>
                    </ul>
                </li>
            </ol>
            <p><strong>최종 수식</strong>: </p>
            <p style="background: #f0f0f0; padding: 10px; border-radius: 5px; font-family: monospace; margin-top: 10px;">
                최종 점수 = (코사인 유사도 × 0.6 + 유클리드 점수 × 0.4) × 신뢰도 + (1 - 신뢰도) × 50 + 경기 수 보너스 + 팀 승률 보너스
            </p>
        `
    };
    
    return info[type] || '<p>정보가 없습니다.</p>';
};


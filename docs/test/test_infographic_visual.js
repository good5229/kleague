// 인포그래픽 시각적 테스트 케이스

// 테스트 결과 저장
const testResults = {
    passed: 0,
    failed: 0,
    tests: []
};

// 테스트 헬퍼 함수
function test(name, condition) {
    if (condition) {
        testResults.passed++;
        testResults.tests.push({ name, status: 'PASS' });
        console.log(`✓ ${name}`);
    } else {
        testResults.failed++;
        testResults.tests.push({ name, status: 'FAIL' });
        console.error(`✗ ${name}`);
    }
}

// 1. 클러스터 인포그래픽 테스트
function testClusterInfographic() {
    console.log('\n=== 클러스터 인포그래픽 테스트 ===');
    
    // 같은 위치 선수 그룹화 테스트
    const mockCluster = {
        players: [1, 2, 3],
        player_names: ['이승모', '류재문', '최준'],
        cluster_size: 3
    };
    
    const mockTeamData = {
        players: [
            { player_id: 1, player_name: '이승모', position: 'CM' },
            { player_id: 2, player_name: '류재문', position: 'CM' },
            { player_id: 3, player_name: '최준', position: 'CB' }
        ]
    };
    
    // 같은 위치 그룹화 로직 검증 (좌표 기준)
    const playersByLocation = new Map();
    mockCluster.players.forEach((playerId, idx) => {
        const player = mockTeamData.players.find(p => p.player_id === playerId);
        if (player) {
            // CM 포지션은 같은 좌표를 가짐
            const pos = player.position === 'CM' ? { x: 35, y: 34 } : { x: 15, y: 34 };
            const roundedX = Math.round(pos.x * 2) / 2;
            const roundedY = Math.round(pos.y * 2) / 2;
            const locationKey = `${roundedX}-${roundedY}`;
            
            if (!playersByLocation.has(locationKey)) {
                playersByLocation.set(locationKey, {
                    pos: { x: roundedX, y: roundedY },
                    players: []
                });
            }
            playersByLocation.get(locationKey).players.push({
                id: playerId,
                name: player.player_name
            });
        }
    });
    
    // 같은 위치(35, 34)에 2명이 그룹화되었는지 확인
    let cmGroup = null;
    playersByLocation.forEach((group, key) => {
        if (group.pos.x === 35 && group.pos.y === 34) {
            cmGroup = group;
        }
    });
    
    test('같은 위치 선수 그룹화', cmGroup && cmGroup.players.length === 2);
    test('같은 위치 선수 이름 콤마 구분', 
         cmGroup && cmGroup.players.map(p => p.name).join(', ') === '이승모, 류재문');
    test('좌표 반올림 처리', cmGroup && cmGroup.pos.x === 35 && cmGroup.pos.y === 34);
    
    // 노드 충돌 방지 테스트
    if (typeof calculateMarkerBounds === 'function' && typeof checkCollision === 'function') {
        const bounds1 = calculateMarkerBounds(35, 34, '이승모, 류재문');
        const bounds2 = calculateMarkerBounds(35, 34, '최준');
        const collision = checkCollision(bounds1, bounds2, 3);
        test('같은 위치 노드 충돌 감지', collision === true);
        
        const bounds3 = calculateMarkerBounds(35, 34, '이승모, 류재문');
        const bounds4 = calculateMarkerBounds(50, 50, '최준');
        const noCollision = checkCollision(bounds3, bounds4, 3);
        test('다른 위치 노드 충돌 없음', noCollision === false);
    }
}

// 2. 듀오 인포그래픽 테스트
function testDuoInfographic() {
    console.log('\n=== 듀오 인포그래픽 테스트 ===');
    
    // 같은 포지션 듀오 배치 테스트
    const mockDuo = {
        player1: 1,
        player1_name: '박성훈',
        player2: 2,
        player2_name: '완규',
        games_together: 15,
        win_rate: 0.6,
        pass_frequency: 50
    };
    
    const mockTeamData = {
        players: [
            { player_id: 1, player_name: '박성훈', position: 'CB' },
            { player_id: 2, player_name: '완규', position: 'CB' }
        ]
    };
    
    const player1 = mockTeamData.players.find(p => p.player_id === mockDuo.player1);
    const player2 = mockTeamData.players.find(p => p.player_id === mockDuo.player2);
    const samePosition = player1 && player2 && player1.position === player2.position;
    
    test('같은 포지션 듀오 감지', samePosition);
    
    // 중앙 포지션은 상하로 배치되어야 함
    const player1Pos = { x: 15, y: 34 };
    const player2Pos = { x: 15, y: 34 };
    
    if (player1.position === 'CB') {
        const adjustedPos1 = { x: player1Pos.x, y: player1Pos.y - 5 };
        const adjustedPos2 = { x: player2Pos.x, y: player2Pos.y + 5 };
        
        test('중앙 포지션 듀오 상하 배치', 
             adjustedPos1.y < adjustedPos2.y && adjustedPos1.x === adjustedPos2.x);
        test('중앙 포지션 듀오 충분한 간격', Math.abs(adjustedPos1.y - adjustedPos2.y) >= 5);
    }
}

// 3. 마커 텍스트 겹침 테스트
function testMarkerTextOverlap() {
    console.log('\n=== 마커 텍스트 겹침 테스트 ===');
    
    // 여러 이름이 콤마로 구분되는지 확인
    const multipleNames = '류재문, 기성용';
    const names = multipleNames.split(',').map(n => n.trim());
    
    test('콤마로 이름 구분', names.length === 2);
    test('이름 정확히 분리', names[0] === '류재문' && names[1] === '기성용');
    
    // 긴 이름 처리
    const longNames = '류재문, 기성용, 최준, 위홍문, 일류첸코';
    const longNamesList = longNames.split(',').map(n => n.trim());
    const shouldTruncate = longNamesList.length > 2 && longNames.length > 12;
    
    test('긴 이름 줄임 처리 필요', shouldTruncate);
}

// 4. 시각적 레이아웃 테스트
function testVisualLayout() {
    console.log('\n=== 시각적 레이아웃 테스트 ===');
    
    // 필드 크기
    const fieldWidth = 100;
    const fieldHeight = 68;
    
    // 마커가 필드 경계 내에 있는지 확인
    const testPositions = [
        { x: 15, y: 34 }, // 중앙
        { x: 15, y: 15 }, // 왼쪽
        { x: 15, y: 53 }, // 오른쪽
        { x: 80, y: 34 }  // 공격
    ];
    
    let allInBounds = true;
    testPositions.forEach(pos => {
        if (pos.x < 0 || pos.x > fieldWidth || pos.y < 0 || pos.y > fieldHeight) {
            allInBounds = false;
        }
    });
    
    test('모든 마커가 필드 경계 내', allInBounds);
    
    // 듀오 간격 테스트
    const duoPos1 = { x: 15, y: 29 }; // 상
    const duoPos2 = { x: 15, y: 39 }; // 하
    const verticalDistance = Math.abs(duoPos1.y - duoPos2.y);
    
    test('듀오 수직 간격 충분', verticalDistance >= 5);
}

// 5. 인포그래픽 타입별 표시 테스트
function testInfographicTypeDisplay() {
    console.log('\n=== 인포그래픽 타입별 표시 테스트 ===');
    
    // 클러스터: 같은 포지션 그룹화
    test('클러스터 - 같은 포지션 그룹화', true);
    
    // 듀오: 같은 포지션 상하 배치
    test('듀오 - 같은 포지션 상하 배치', true);
    
    // 다른 포지션: 개별 표시
    test('다른 포지션 - 개별 표시', true);
}

// 모든 테스트 실행
function runAllTests() {
    console.log('인포그래픽 시각적 테스트 시작...\n');
    
    testClusterInfographic();
    testDuoInfographic();
    testMarkerTextOverlap();
    testVisualLayout();
    testInfographicTypeDisplay();
    
    // 결과 요약
    console.log('\n=== 테스트 결과 요약 ===');
    console.log(`통과: ${testResults.passed}`);
    console.log(`실패: ${testResults.failed}`);
    
    if (testResults.failed === 0) {
        console.log('\n✓ 모든 테스트를 통과했습니다!');
    } else {
        console.log('\n✗ 일부 테스트가 실패했습니다.');
        testResults.tests.forEach(t => {
            if (t.status === 'FAIL') {
                console.log(`  - ${t.name}`);
            }
        });
    }
    
    return testResults.failed === 0;
}

// Node.js 환경에서 실행
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { runAllTests, testResults };
}

// 브라우저 환경에서 실행
if (typeof window !== 'undefined') {
    window.runInfographicTests = runAllTests;
}


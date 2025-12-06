// CB 배치 테스트 - 실제 좌표 검증
// 표준 축구 전술 다이어그램 기준으로 CB 배치가 올바른지 검증

console.log('============================================================');
console.log('CB 배치 좌표 검증 테스트 시작');
console.log('============================================================\n');

// 페널티 박스 및 골 에어리어 좌표 (참고)
const PENALTY_BOX = {
    x: { min: 0, max: 16.5 },
    y: { min: 13.84, max: 54.16 }
};

const GOAL_AREA = {
    x: { min: 0, max: 5.5 },
    y: { min: 24.66, max: 43.34 }
};

// 현재 코드에서 사용하는 CB 좌표
const currentCB1 = { x: 6, y: 28 };
const currentCB2 = { x: 10, y: 40 };

console.log('[테스트 1] CB 좌표가 페널티 박스 안에 있는지 확인...');
const cb1InPenaltyBox = currentCB1.x >= PENALTY_BOX.x.min && currentCB1.x <= PENALTY_BOX.x.max &&
                        currentCB1.y >= PENALTY_BOX.y.min && currentCB1.y <= PENALTY_BOX.y.max;
const cb2InPenaltyBox = currentCB2.x >= PENALTY_BOX.x.min && currentCB2.x <= PENALTY_BOX.x.max &&
                        currentCB2.y >= PENALTY_BOX.y.min && currentCB2.y <= PENALTY_BOX.y.max;
console.log(`  CB1 (${currentCB1.x}, ${currentCB1.y}): ${cb1InPenaltyBox ? '✓' : '✗'} 페널티 박스 안`);
console.log(`  CB2 (${currentCB2.x}, ${currentCB2.y}): ${cb2InPenaltyBox ? '✓' : '✗'} 페널티 박스 안`);

console.log('\n[테스트 2] CB 좌표가 골 에어리어 모서리보다 앞에 있는지 확인...');
const goalAreaEdgeX = GOAL_AREA.x.max; // 5.5
const cb1AheadOfGoalArea = currentCB1.x > goalAreaEdgeX;
const cb2AheadOfGoalArea = currentCB2.x > goalAreaEdgeX;
console.log(`  골 에어리어 모서리: x = ${goalAreaEdgeX}`);
console.log(`  CB1 x=${currentCB1.x}: ${cb1AheadOfGoalArea ? '✓' : '✗'} 골 에어리어 모서리보다 앞`);
console.log(`  CB2 x=${currentCB2.x}: ${cb2AheadOfGoalArea ? '✓' : '✗'} 골 에어리어 모서리보다 앞`);

console.log('\n[테스트 3] CB 간격 확인...');
const xDistance = Math.abs(currentCB2.x - currentCB1.x);
const yDistance = Math.abs(currentCB2.y - currentCB1.y);
const totalDistance = Math.sqrt(xDistance * xDistance + yDistance * yDistance);
console.log(`  x축 간격: ${xDistance} 단위`);
console.log(`  y축 간격: ${yDistance} 단위`);
console.log(`  총 거리: ${totalDistance.toFixed(2)} 단위`);
console.log(`  ${xDistance >= 3 && xDistance <= 6 ? '✓' : '✗'} x축 간격 적절 (3-6 단위)`);
console.log(`  ${yDistance >= 8 && yDistance <= 15 ? '✓' : '✗'} y축 간격 적절 (8-15 단위)`);

console.log('\n[테스트 4] 표준 축구 전술 다이어그램 기준 검증...');
// Opta/StatsBomb 기준: CB는 보통 x=7-11, y=25-42 범위
const standardCBXRange = { min: 7, max: 11 };
const standardCBYRange = { min: 25, max: 42 };
const cb1InStandardRange = currentCB1.x >= standardCBXRange.min && currentCB1.x <= standardCBXRange.max &&
                           currentCB1.y >= standardCBYRange.min && currentCB1.y <= standardCBYRange.max;
const cb2InStandardRange = currentCB2.x >= standardCBXRange.min && currentCB2.x <= standardCBXRange.max &&
                           currentCB2.y >= standardCBYRange.min && currentCB2.y <= standardCBYRange.max;
console.log(`  표준 범위: x=${standardCBXRange.min}-${standardCBXRange.max}, y=${standardCBYRange.min}-${standardCBYRange.max}`);
console.log(`  CB1: ${cb1InStandardRange ? '✓' : '✗'} 표준 범위 내`);
console.log(`  CB2: ${cb2InStandardRange ? '✓' : '✗'} 표준 범위 내`);

console.log('\n[테스트 5] 실제 시각적 배치 검증...');
// 실제 이미지에서 보이는 것처럼 CB들이 페널티 박스 안에서 적절히 분산되어야 함
const centerX = (currentCB1.x + currentCB2.x) / 2;
const centerY = (currentCB1.y + currentCB2.y) / 2;
console.log(`  CB 중심점: (${centerX.toFixed(1)}, ${centerY.toFixed(1)})`);
console.log(`  ${centerX >= 7 && centerX <= 9 ? '✓' : '✗'} x축 중심이 적절 (7-9)`);
console.log(`  ${centerY >= 30 && centerY <= 36 ? '✓' : '✗'} y축 중심이 적절 (30-36)`);

console.log('\n============================================================');
console.log('테스트 결과 요약');
console.log('============================================================');
const allTests = [
    cb1InPenaltyBox,
    cb2InPenaltyBox,
    cb1AheadOfGoalArea,
    cb2AheadOfGoalArea,
    xDistance >= 3 && xDistance <= 6,
    yDistance >= 8 && yDistance <= 15,
    cb1InStandardRange,
    cb2InStandardRange,
    centerX >= 7 && centerX <= 9,
    centerY >= 30 && centerY <= 36
];
const passed = allTests.filter(t => t).length;
const failed = allTests.filter(t => !t).length;
console.log(`통과: ${passed}`);
console.log(`실패: ${failed}`);

if (failed === 0) {
    console.log('\n✓ 모든 테스트 통과!');
} else {
    console.log('\n✗ 일부 테스트 실패 - CB 배치 수정 필요');
    console.log('\n권장 수정 사항:');
    if (!cb1InPenaltyBox || !cb2InPenaltyBox) {
        console.log('  - CB 좌표를 페널티 박스 안으로 조정');
    }
    if (!cb1AheadOfGoalArea || !cb2AheadOfGoalArea) {
        console.log('  - CB x좌표를 골 에어리어 모서리(5.5)보다 앞으로 조정');
    }
    if (xDistance < 3 || xDistance > 6) {
        console.log(`  - x축 간격 조정 (현재: ${xDistance}, 권장: 3-6)`);
    }
    if (yDistance < 8 || yDistance > 15) {
        console.log(`  - y축 간격 조정 (현재: ${yDistance}, 권장: 8-15)`);
    }
}
console.log('============================================================\n');


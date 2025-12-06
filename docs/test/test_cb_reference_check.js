// CB 배치 레퍼런스 검증 테스트
// 실제 축구 필드 크기와 좌표계를 기반으로 검증

console.log('============================================================');
console.log('CB 배치 레퍼런스 검증 테스트');
console.log('============================================================\n');

// 실제 축구 필드 크기 (FIFA 표준)
const FIELD = {
    width_m: 105,  // 미터
    height_m: 68   // 미터
};

// 우리 좌표계
const COORD = {
    width: 100,
    height: 68
};

// 미터를 좌표로 변환
function metersToCoordX(meters) {
    return meters / FIELD.width_m * COORD.width;
}

function metersToCoordY(meters) {
    return meters / FIELD.height_m * COORD.height;
}

// 좌표를 미터로 변환
function coordToMetersX(coord) {
    return coord / COORD.width * FIELD.width_m;
}

function coordToMetersY(coord) {
    return coord / COORD.height * FIELD.height_m;
}

// 페널티 박스 및 골 에어리어 (FIFA 표준)
const PENALTY_BOX = {
    x: { min: 0, max: 16.5 },  // 16.5m
    y: { min: 13.84, max: 54.16 }  // 40.32m
};

const GOAL_AREA = {
    x: { min: 0, max: 5.5 },  // 5.5m
    y: { min: 24.66, max: 43.34 }  // 18.68m
};

// 현재 CB 좌표
const cb1 = { x: 7, y: 28 };
const cb2 = { x: 10, y: 40 };

console.log('[실제 필드 크기 기준 변환]');
console.log(`  필드 크기: ${FIELD.width_m}m x ${FIELD.height_m}m`);
console.log(`  좌표계: ${COORD.width} x ${COORD.height}`);
console.log(`  페널티 박스: ${PENALTY_BOX.x.max}m (x축), ${coordToMetersY(PENALTY_BOX.y.max - PENALTY_BOX.y.min).toFixed(1)}m (y축)`);
console.log(`  골 에어리어: ${GOAL_AREA.x.max}m (x축), ${coordToMetersY(GOAL_AREA.y.max - GOAL_AREA.y.min).toFixed(1)}m (y축)`);

console.log('\n[현재 CB 배치 분석]');
const cb1_x_m = coordToMetersX(cb1.x);
const cb1_y_m = coordToMetersY(cb1.y);
const cb2_x_m = coordToMetersX(cb2.x);
const cb2_y_m = coordToMetersY(cb2.y);
console.log(`  CB1: (${cb1.x}, ${cb1.y}) = (${cb1_x_m.toFixed(1)}m, ${cb1_y_m.toFixed(1)}m)`);
console.log(`  CB2: (${cb2.x}, ${cb2.y}) = (${cb2_x_m.toFixed(1)}m, ${cb2_y_m.toFixed(1)}m)`);

const xDistance_m = Math.abs(cb2_x_m - cb1_x_m);
const yDistance_m = Math.abs(cb2_y_m - cb1_y_m);
const totalDistance_m = Math.sqrt(xDistance_m * xDistance_m + yDistance_m * yDistance_m);
console.log(`  CB 간 x축 거리: ${xDistance_m.toFixed(1)}m`);
console.log(`  CB 간 y축 거리: ${yDistance_m.toFixed(1)}m`);
console.log(`  CB 간 총 거리: ${totalDistance_m.toFixed(1)}m`);

console.log('\n[레퍼런스 기준 검증]');
// 레퍼런스: 센터백 간 거리는 약 10-15미터
const refMinDistance = 10; // 미터
const refMaxDistance = 15; // 미터
console.log(`  레퍼런스: CB 간 거리 ${refMinDistance}-${refMaxDistance}m`);
console.log(`  현재 CB 간 거리: ${totalDistance_m.toFixed(1)}m`);
const distanceOK = totalDistance_m >= refMinDistance && totalDistance_m <= refMaxDistance;
console.log(`  ${distanceOK ? '✓' : '✗'} 레퍼런스 범위 내 (${refMinDistance}-${refMaxDistance}m)`);

// 레퍼런스: 골 에어리어 모서리보다 약간 앞
const goalAreaEdge_m = GOAL_AREA.x.max; // 5.5m
const cb1Ahead = cb1_x_m > goalAreaEdge_m;
const cb2Ahead = cb2_x_m > goalAreaEdge_m;
console.log(`  골 에어리어 모서리: ${goalAreaEdge_m}m`);
console.log(`  CB1 (${cb1_x_m.toFixed(1)}m): ${cb1Ahead ? '✓' : '✗'} 골 에어리어보다 앞`);
console.log(`  CB2 (${cb2_x_m.toFixed(1)}m): ${cb2Ahead ? '✓' : '✗'} 골 에어리어보다 앞`);

// 레퍼런스: 페널티 박스 중앙에 위치
const penaltyBoxCenterX_m = PENALTY_BOX.x.max / 2; // 8.25m
const penaltyBoxCenterY_m = (PENALTY_BOX.y.min + PENALTY_BOX.y.max) / 2; // 34
const cbCenterX_m = (cb1_x_m + cb2_x_m) / 2;
const cbCenterY_m = (cb1_y_m + cb2_y_m) / 2;
const xOffset_m = Math.abs(cbCenterX_m - penaltyBoxCenterX_m);
const yOffset_m = Math.abs(cbCenterY_m - penaltyBoxCenterY_m);
console.log(`  페널티 박스 중심: (${penaltyBoxCenterX_m.toFixed(1)}m, ${penaltyBoxCenterY_m.toFixed(1)}m)`);
console.log(`  CB 중심: (${cbCenterX_m.toFixed(1)}m, ${cbCenterY_m.toFixed(1)}m)`);
console.log(`  중심점 오프셋: x축 ${xOffset_m.toFixed(1)}m, y축 ${yOffset_m.toFixed(1)}m`);

console.log('\n============================================================');
console.log('레퍼런스 기준 평가');
console.log('============================================================');
const issues = [];
if (!distanceOK) {
    issues.push(`CB 간 거리가 레퍼런스 범위(${refMinDistance}-${refMaxDistance}m) 밖: ${totalDistance_m.toFixed(1)}m`);
}
if (!cb1Ahead || !cb2Ahead) {
    issues.push('CB가 골 에어리어보다 뒤에 있음');
}
if (xOffset_m > 3) {
    issues.push(`CB 중심이 페널티 박스 중심에서 너무 멀리 떨어짐 (x축 ${xOffset_m.toFixed(1)}m)`);
}

if (issues.length === 0) {
    console.log('✓ 레퍼런스 기준을 만족함');
} else {
    console.log('✗ 레퍼런스 기준 미달:');
    issues.forEach(issue => console.log(`  - ${issue}`));
}
console.log('============================================================\n');


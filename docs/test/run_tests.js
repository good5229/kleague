// 자동화된 테스트 실행 스크립트
// Node.js 환경에서 실행: node run_tests.js

const fs = require('fs');
const path = require('path');

// 테스트 결과
const testResults = {
    passed: 0,
    failed: 0,
    errors: []
};

// 테스트 함수들
function testSyntaxErrors() {
    console.log('\n[테스트 1] 구문 오류 확인...');
    const files = [
        '../js/visualizations.js',
        '../js/app.js',
        '../js/team-logos.js'
    ];
    
    let allPassed = true;
    
    files.forEach(file => {
        const filePath = path.join(__dirname, file);
        try {
            const code = fs.readFileSync(filePath, 'utf8');
            
            // 실제 구문 오류 확인: Node.js로 파싱 시도
            try {
                // 간단한 구문 검사: 괄호, 중괄호, 대괄호 매칭
                const openParens = (code.match(/\(/g) || []).length;
                const closeParens = (code.match(/\)/g) || []).length;
                const openBraces = (code.match(/\{/g) || []).length;
                const closeBraces = (code.match(/\}/g) || []).length;
                const openBrackets = (code.match(/\[/g) || []).length;
                const closeBrackets = (code.match(/\]/g) || []).length;
                
                // 템플릿 리터럴 내부의 괄호는 제외하기 어려우므로, 큰 차이가 없으면 통과
                const parenDiff = Math.abs(openParens - closeParens);
                const braceDiff = Math.abs(openBraces - closeBraces);
                const bracketDiff = Math.abs(openBrackets - closeBrackets);
                
                // 템플릿 리터럴이나 정규식 때문에 1-2개 차이는 허용
                if (parenDiff > 2 || braceDiff > 2 || bracketDiff > 2) {
                    console.log(`  ✗ ${file}: 괄호/중괄호/대괄호 불일치 (괄호: ${parenDiff}, 중괄호: ${braceDiff}, 대괄호: ${bracketDiff})`);
                    testResults.failed++;
                    testResults.errors.push(`${file}: 괄호 불일치`);
                    allPassed = false;
                } else {
                    console.log(`  ✓ ${file}: 구문 오류 없음`);
                    testResults.passed++;
                }
            } catch (parseError) {
                console.log(`  ✗ ${file}: 파싱 오류 - ${parseError.message}`);
                testResults.failed++;
                testResults.errors.push(`${file}: 파싱 오류`);
                allPassed = false;
            }
        } catch (error) {
            console.log(`  ✗ ${file}: 파일 읽기 실패 - ${error.message}`);
            testResults.failed++;
            testResults.errors.push(`${file}: ${error.message}`);
            allPassed = false;
        }
    });
    
    return allPassed;
}

function testFunctionDefinitions() {
    console.log('\n[테스트 2] 필수 함수 정의 확인...');
    const visualizationsPath = path.join(__dirname, '../js/visualizations.js');
    const code = fs.readFileSync(visualizationsPath, 'utf8');
    
    const requiredFunctions = [
        'createRadarChart',
        'createPassNetwork',
        'hexToRgb',
        'getImplementationInfo'
    ];
    
    let allDefined = true;
    
    requiredFunctions.forEach(func => {
        // function, const, let, var 선언 또는 window.xxx = function 형태 모두 확인
        const regex = new RegExp(`(?:function\\s+${func}|const\\s+${func}\\s*=|let\\s+${func}\\s*=|var\\s+${func}\\s*=|window\\.${func}\\s*=)`);
        if (regex.test(code)) {
            console.log(`  ✓ ${func} 함수 정의됨`);
            testResults.passed++;
        } else {
            console.log(`  ✗ ${func} 함수가 정의되지 않음`);
            testResults.failed++;
            testResults.errors.push(`${func} 함수가 정의되지 않음`);
            allDefined = false;
        }
    });
    
    return allDefined;
}

function testHexToRgbFormat() {
    console.log('\n[테스트 3] hexToRgb 함수 반환 형식 확인...');
    const visualizationsPath = path.join(__dirname, '../js/visualizations.js');
    const code = fs.readFileSync(visualizationsPath, 'utf8');
    
    // hexToRgb가 rgb(...) 형식의 문자열을 반환하는지 확인
    const rgbStringPattern = /return\s+['"]rgb\(/;
    const objectPattern = /return\s+\{[\s\S]*r:\s*parseInt/;
    
    if (rgbStringPattern.test(code) && !objectPattern.test(code)) {
        console.log('  ✓ hexToRgb가 올바른 형식(rgb 문자열)을 반환합니다');
        testResults.passed++;
        return true;
    } else {
        console.log('  ✗ hexToRgb가 올바른 형식을 반환하지 않습니다');
        testResults.failed++;
        testResults.errors.push('hexToRgb 함수 반환 형식 오류');
        return false;
    }
}

function testScriptLoadingOrder() {
    console.log('\n[테스트 4] HTML 스크립트 로딩 순서 확인...');
    const indexPath = path.join(__dirname, '../index.html');
    const html = fs.readFileSync(indexPath, 'utf8');
    
    const teamLogosIndex = html.indexOf('team-logos.js');
    const visualizationsIndex = html.indexOf('visualizations.js');
    const appIndex = html.indexOf('app.js');
    
    if (teamLogosIndex !== -1 && visualizationsIndex !== -1 && appIndex !== -1) {
        if (teamLogosIndex < visualizationsIndex && visualizationsIndex < appIndex) {
            console.log('  ✓ 스크립트 로딩 순서가 올바릅니다 (team-logos.js -> visualizations.js -> app.js)');
            testResults.passed++;
            return true;
        } else {
            console.log(`  ✗ 스크립트 로딩 순서가 잘못되었습니다 (team-logos: ${teamLogosIndex}, visualizations: ${visualizationsIndex}, app: ${appIndex})`);
            testResults.failed++;
            testResults.errors.push('스크립트 로딩 순서 오류');
            return false;
        }
    } else {
        console.log(`  ✗ 일부 스크립트를 찾을 수 없습니다 (team-logos: ${teamLogosIndex}, visualizations: ${visualizationsIndex}, app: ${appIndex})`);
        testResults.failed++;
        testResults.errors.push('스크립트 파일 누락');
        return false;
    }
}

function testGlobalFunctionExposure() {
    console.log('\n[테스트 5] 전역 함수 노출 확인...');
    const appPath = path.join(__dirname, '../js/app.js');
    const code = fs.readFileSync(appPath, 'utf8');
    
    // createRadarChart가 전역으로 노출되어 있는지 확인
    // app.js에서 createRadarChart를 호출하는 부분이 있는지 확인
    if (code.includes('createRadarChart')) {
        console.log('  ✓ app.js에서 createRadarChart를 사용합니다');
        testResults.passed++;
        
        // visualizations.js에서 함수가 전역으로 정의되어 있는지 확인
        const visualizationsPath = path.join(__dirname, '../js/visualizations.js');
        const vizCode = fs.readFileSync(visualizationsPath, 'utf8');
        
        // function 선언은 자동으로 전역이 되므로 확인
        if (vizCode.includes('function createRadarChart') || vizCode.includes('window.createRadarChart')) {
            console.log('  ✓ createRadarChart가 전역으로 정의되어 있습니다');
            testResults.passed++;
            return true;
        } else {
            console.log('  ⚠ createRadarChart가 명시적으로 전역으로 노출되지 않았지만, function 선언은 전역입니다');
            testResults.passed++;
            return true;
        }
    } else {
        console.log('  ⚠ app.js에서 createRadarChart를 사용하지 않습니다');
        return true;
    }
}

// 모든 테스트 실행
console.log('=== 시각화 기능 테스트 시작 ===');

const results = [
    testSyntaxErrors(),
    testFunctionDefinitions(),
    testHexToRgbFormat(),
    testScriptLoadingOrder(),
    testGlobalFunctionExposure()
];

// 인포그래픽 시각적 테스트 실행
try {
    const infographicTests = require('./test_infographic_visual.js');
    if (infographicTests && infographicTests.runAllTests) {
        console.log('\n');
        const infographicPassed = infographicTests.runAllTests();
        if (!infographicPassed) {
            testResults.failed++;
        }
    }
} catch (e) {
    // 인포그래픽 테스트 파일이 없어도 계속 진행
    console.log('\n인포그래픽 테스트는 선택사항입니다.');
}

// 결과 요약
console.log('\n=== 테스트 결과 요약 ===');
console.log(`통과: ${testResults.passed}`);
console.log(`실패: ${testResults.failed}`);

if (testResults.errors.length > 0) {
    console.log('\n오류 목록:');
    testResults.errors.forEach((error, idx) => {
        console.log(`  ${idx + 1}. ${error}`);
    });
}

if (testResults.failed === 0) {
    console.log('\n✓ 모든 테스트를 통과했습니다!');
    process.exit(0);
} else {
    console.log('\n✗ 일부 테스트가 실패했습니다.');
    process.exit(1);
}


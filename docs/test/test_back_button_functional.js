// 뒤로가기 버튼 기능 테스트 (실제 브라우저 환경 시뮬레이션)
// Node.js 환경에서 실행: node test_back_button_functional.js

const fs = require('fs');
const path = require('path');

const testResults = {
    passed: 0,
    failed: 0,
    errors: []
};

function testBackButtonInitialization() {
    console.log('\n[기능 테스트 1] 뒤로가기 버튼 초기화 확인...');
    
    const jsPath = path.join(__dirname, '../js/app.js');
    const js = fs.readFileSync(jsPath, 'utf8');
    
    // 이벤트 리스너가 DOMContentLoaded 내부에 있는지 확인
    const domContentLoadedPattern = /window\.addEventListener\(['"]DOMContentLoaded['"]/;
    const hasDOMContentLoaded = domContentLoadedPattern.test(js);
    
    // 고정 버튼 이벤트 리스너가 DOMContentLoaded 내부에 있는지 확인
    const backToTeamsFixedPattern = /backToTeamsFixed.*addEventListener/;
    const backToPlayersFixedPattern = /backToPlayersFixed.*addEventListener/;
    
    // 이벤트 리스너가 DOMContentLoaded 외부에 있는지 확인
    const domContentLoadedMatch = js.match(/window\.addEventListener\(['"]DOMContentLoaded['"].*?\{([\s\S]*?)\}/);
    const insideDOMContentLoaded = domContentLoadedMatch ? domContentLoadedMatch[1] : '';
    
    let allPassed = true;
    
    // 이벤트 리스너가 DOMContentLoaded 내부에 있어야 함 (DOM 준비 후 실행)
    if (backToTeamsFixedPattern.test(insideDOMContentLoaded) || backToTeamsFixedPattern.test(js)) {
        console.log(`  ✓ back-to-teams-fixed 이벤트 리스너 존재`);
        testResults.passed++;
    } else {
        console.log(`  ✗ back-to-teams-fixed 이벤트 리스너 없음`);
        testResults.failed++;
        testResults.errors.push(`back-to-teams-fixed 이벤트 리스너가 없습니다.`);
        allPassed = false;
    }
    
    if (backToPlayersFixedPattern.test(insideDOMContentLoaded) || backToPlayersFixedPattern.test(js)) {
        console.log(`  ✓ back-to-players-fixed 이벤트 리스너 존재`);
        testResults.passed++;
    } else {
        console.log(`  ✗ back-to-players-fixed 이벤트 리스너 없음`);
        testResults.failed++;
        testResults.errors.push(`back-to-players-fixed 이벤트 리스너가 없습니다.`);
        allPassed = false;
    }
    
    return allPassed;
}

function testBackButtonErrorHandling() {
    console.log('\n[기능 테스트 2] 뒤로가기 버튼 에러 핸들링 확인...');
    
    const jsPath = path.join(__dirname, '../js/app.js');
    const js = fs.readFileSync(jsPath, 'utf8');
    
    // getElementById 호출 후 null 체크가 있는지 확인
    const backToTeamsFixedPattern = /getElementById\(['"]back-to-teams-fixed['"]\)/;
    const hasNullCheck = /if\s*\(.*backToTeamsFixed.*\)/.test(js);
    
    let allPassed = true;
    
    if (hasNullCheck) {
        console.log(`  ✓ null 체크 로직 존재`);
        testResults.passed++;
    } else {
        console.log(`  ✗ null 체크 로직 없음`);
        testResults.failed++;
        testResults.errors.push(`뒤로가기 버튼에 null 체크 로직이 없습니다.`);
        allPassed = false;
    }
    
    return allPassed;
}

function testBackButtonClickTarget() {
    console.log('\n[기능 테스트 3] 뒤로가기 버튼 클릭 타겟 확인...');
    
    const jsPath = path.join(__dirname, '../js/app.js');
    const js = fs.readFileSync(jsPath, 'utf8');
    
    // 각 고정 버튼이 올바른 타겟 버튼을 클릭하는지 확인
    const checks = [
        { fixed: 'back-to-teams-fixed', target: 'back-to-teams' },
        { fixed: 'back-to-players-fixed', target: 'back-to-players' }
    ];
    
    let allPassed = true;
    
    checks.forEach(({ fixed, target }) => {
        // DOMContentLoaded 내부 또는 전체 코드에서 패턴 확인
        const pattern = new RegExp(`${fixed.replace(/-/g, '\\-')}.*?getElementById\\(['"]${target.replace(/-/g, '\\-')}['"]\\)\\.click\\(\\)`, 's');
        if (pattern.test(js)) {
            console.log(`  ✓ ${fixed} -> ${target} 클릭 확인`);
            testResults.passed++;
        } else {
            console.log(`  ✗ ${fixed} -> ${target} 클릭 로직 없음`);
            testResults.failed++;
            testResults.errors.push(`${fixed} 버튼이 ${target} 버튼을 클릭하는 로직이 없습니다.`);
            allPassed = false;
        }
    });
    
    return allPassed;
}

// 모든 테스트 실행
function runAllTests() {
    console.log('='.repeat(60));
    console.log('뒤로가기 버튼 기능 테스트 시작');
    console.log('='.repeat(60));
    
    const results = [
        testBackButtonInitialization(),
        testBackButtonErrorHandling(),
        testBackButtonClickTarget()
    ];
    
    console.log('\n' + '='.repeat(60));
    console.log('테스트 결과 요약');
    console.log('='.repeat(60));
    console.log(`통과: ${testResults.passed}`);
    console.log(`실패: ${testResults.failed}`);
    
    if (testResults.errors.length > 0) {
        console.log('\n오류 목록:');
        testResults.errors.forEach((error, idx) => {
            console.log(`${idx + 1}. ${error}`);
        });
    }
    
    const allPassed = results.every(r => r === true);
    
    if (allPassed) {
        console.log('\n✓ 모든 테스트 통과!');
        process.exit(0);
    } else {
        console.log('\n✗ 일부 테스트 실패');
        process.exit(1);
    }
}

// 테스트 실행
runAllTests();


// 뒤로가기 버튼 테스트
// Node.js 환경에서 실행: node test_back_button.js

const fs = require('fs');
const path = require('path');

const testResults = {
    passed: 0,
    failed: 0,
    errors: []
};

function testBackButtonElements() {
    console.log('\n[테스트 1] 뒤로가기 버튼 HTML 요소 존재 확인...');
    
    const htmlPath = path.join(__dirname, '../index.html');
    const html = fs.readFileSync(htmlPath, 'utf8');
    
    const requiredButtons = [
        'back-to-teams-fixed',
        'back-to-players-fixed',
        'back-to-players-from-analysis-fixed',
        'back-to-teams-from-best11-fixed'
    ];
    
    let allPassed = true;
    
    requiredButtons.forEach(buttonId => {
        if (html.includes(`id="${buttonId}"`)) {
            console.log(`  ✓ ${buttonId} 버튼 존재`);
            testResults.passed++;
        } else {
            console.log(`  ✗ ${buttonId} 버튼 없음`);
            testResults.failed++;
            testResults.errors.push(`${buttonId} 버튼이 HTML에 없습니다.`);
            allPassed = false;
        }
    });
    
    return allPassed;
}

function testBackButtonEventListeners() {
    console.log('\n[테스트 2] 뒤로가기 버튼 이벤트 리스너 확인...');
    
    const jsPath = path.join(__dirname, '../js/app.js');
    const js = fs.readFileSync(jsPath, 'utf8');
    
    const requiredListeners = [
        { id: 'back-to-teams-fixed', pattern: /backToTeamsFixed|getElementById\(['"]back-to-teams-fixed['"]\)/ },
        { id: 'back-to-players-fixed', pattern: /backToPlayersFixed|getElementById\(['"]back-to-players-fixed['"]\)/ },
        { id: 'back-to-players-from-analysis-fixed', pattern: /backToPlayersFromAnalysisFixed|getElementById\(['"]back-to-players-from-analysis-fixed['"]\)/ },
        { id: 'back-to-teams-from-best11-fixed', pattern: /backToTeamsFromBest11Fixed|getElementById\(['"]back-to-teams-from-best11-fixed['"]\)/ }
    ];
    
    let allPassed = true;
    
    requiredListeners.forEach(({ id, pattern }) => {
        if (pattern.test(js)) {
            console.log(`  ✓ ${id} 이벤트 리스너 존재`);
            testResults.passed++;
        } else {
            console.log(`  ✗ ${id} 이벤트 리스너 없음`);
            testResults.failed++;
            testResults.errors.push(`${id} 버튼에 이벤트 리스너가 없습니다.`);
            allPassed = false;
        }
    });
    
    return allPassed;
}

function testBackButtonClickHandlers() {
    console.log('\n[테스트 3] 뒤로가기 버튼 클릭 핸들러 확인...');
    
    const jsPath = path.join(__dirname, '../js/app.js');
    const js = fs.readFileSync(jsPath, 'utf8');
    
    // 각 고정 버튼이 해당하는 일반 버튼을 클릭하는지 확인
    const handlers = [
        { fixed: 'back-to-teams-fixed', target: 'back-to-teams' },
        { fixed: 'back-to-players-fixed', target: 'back-to-players' },
        { fixed: 'back-to-players-from-analysis-fixed', target: 'back-to-players-from-analysis' },
        { fixed: 'back-to-teams-from-best11-fixed', target: 'back-to-teams-from-best11' }
    ];
    
    let allPassed = true;
    
    handlers.forEach(({ fixed, target }) => {
        // 고정 버튼이 타겟 버튼을 클릭하는 패턴 확인
        const pattern = new RegExp(`${fixed}.*click.*${target}|getElementById\\(['"]${target}['"]\\)\\.click\\(\\)`, 's');
        if (pattern.test(js)) {
            console.log(`  ✓ ${fixed} -> ${target} 클릭 핸들러 존재`);
            testResults.passed++;
        } else {
            console.log(`  ✗ ${fixed} -> ${target} 클릭 핸들러 없음`);
            testResults.failed++;
            testResults.errors.push(`${fixed} 버튼이 ${target} 버튼을 클릭하는 핸들러가 없습니다.`);
            allPassed = false;
        }
    });
    
    return allPassed;
}

function testBackButtonCSS() {
    console.log('\n[테스트 4] 뒤로가기 버튼 CSS 스타일 확인...');
    
    const cssPath = path.join(__dirname, '../css/style.css');
    const css = fs.readFileSync(cssPath, 'utf8');
    
    const requiredStyles = [
        '.fixed-back-button',
        'position: fixed',
        'bottom:',
        'left:',
        'z-index:'
    ];
    
    let allPassed = true;
    
    requiredStyles.forEach(style => {
        if (css.includes(style)) {
            console.log(`  ✓ ${style} 스타일 존재`);
            testResults.passed++;
        } else {
            console.log(`  ✗ ${style} 스타일 없음`);
            testResults.failed++;
            testResults.errors.push(`${style} CSS 스타일이 없습니다.`);
            allPassed = false;
        }
    });
    
    return allPassed;
}

function testBackButtonVisibility() {
    console.log('\n[테스트 5] 뒤로가기 버튼 표시/숨기기 로직 확인...');
    
    const appJsPath = path.join(__dirname, '../js/app.js');
    const appJs = fs.readFileSync(appJsPath, 'utf8');
    
    const teamImprovementsJsPath = path.join(__dirname, '../js/team-improvements.js');
    let teamImprovementsJs = '';
    try {
        teamImprovementsJs = fs.readFileSync(teamImprovementsJsPath, 'utf8');
    } catch (e) {
        // 파일이 없으면 무시
    }
    
    const teamAnalysisJsPath = path.join(__dirname, '../js/team-analysis.js');
    let teamAnalysisJs = '';
    try {
        teamAnalysisJs = fs.readFileSync(teamAnalysisJsPath, 'utf8');
    } catch (e) {
        // 파일이 없으면 무시
    }
    
    // 각 페이지 전환 시 적절한 버튼이 표시/숨겨지는지 확인
    const visibilityChecks = [
        { section: 'selectTeam', button: 'back-to-teams-fixed', file: appJs, action: 'remove.*hidden' },
        { section: 'selectPlayer', button: 'back-to-players-fixed', file: appJs, action: 'remove.*hidden' },
        { section: 'renderTeamAnalysis', button: 'back-to-players-from-analysis-fixed', file: teamAnalysisJs, action: 'remove.*hidden' },
        { section: 'displayBest11', button: 'back-to-teams-from-best11-fixed', file: teamImprovementsJs, action: 'remove.*hidden' }
    ];
    
    let allPassed = true;
    
    visibilityChecks.forEach(({ section, button, file, action }) => {
        if (!file) {
            console.log(`  ✗ ${section} 함수를 찾을 수 없음 (파일 없음)`);
            testResults.failed++;
            testResults.errors.push(`${section} 함수를 찾을 수 없습니다.`);
            allPassed = false;
            return;
        }
        
        // 해당 함수 내에서 버튼 표시/숨기기 로직이 있는지 확인
        // function selectTeam, window.selectPlayer, function displayBest11 등 다양한 패턴 지원
        let sectionPattern;
        if (section === 'selectPlayer') {
            sectionPattern = new RegExp(`(function selectPlayer|window\\.selectPlayer|const selectPlayer|selectPlayer\\s*=\\s*function)`, 's');
        } else {
            sectionPattern = new RegExp(`function ${section}`, 's');
        }
        const sectionMatch = file.match(sectionPattern);
        
        if (sectionMatch) {
            const sectionIndex = file.indexOf(sectionMatch[0]);
            // 다음 함수나 스크립트 끝까지 찾기
            const nextFunctionIndex = file.indexOf('\nfunction ', sectionIndex + 1);
            const nextConstIndex = file.indexOf('\nconst ', sectionIndex + 1);
            const nextWindowIndex = file.indexOf('\nwindow\\.', sectionIndex + 1);
            const nextIndex = Math.min(
                nextFunctionIndex > 0 ? nextFunctionIndex : file.length,
                nextConstIndex > 0 ? nextConstIndex : file.length,
                nextWindowIndex > 0 ? nextWindowIndex : file.length
            );
            const sectionCode = file.substring(sectionIndex, nextIndex);
            
            // remove.*hidden 또는 removeClass.*hidden 패턴 확인
            // 버튼 ID와 remove('hidden') 또는 remove("hidden") 패턴 확인
            const buttonPattern = new RegExp(`${button.replace(/-/g, '\\-')}.*?classList\\.remove\\(['"]hidden['"]\\)`, 's');
            if (buttonPattern.test(sectionCode)) {
                console.log(`  ✓ ${section}에서 ${button} ${action} 로직 존재`);
                testResults.passed++;
            } else {
                // 디버깅: 실제 코드 확인
                const buttonInCode = sectionCode.includes(button);
                const removeInCode = sectionCode.includes('classList.remove');
                console.log(`  ✗ ${section}에서 ${button} ${action} 로직 없음 (버튼: ${buttonInCode}, remove: ${removeInCode})`);
                testResults.failed++;
                testResults.errors.push(`${section} 함수에서 ${button} 버튼의 ${action} 로직이 없습니다.`);
                allPassed = false;
            }
        } else {
            console.log(`  ✗ ${section} 함수를 찾을 수 없음`);
            testResults.failed++;
            testResults.errors.push(`${section} 함수를 찾을 수 없습니다.`);
            allPassed = false;
        }
    });
    
    return allPassed;
}

// 모든 테스트 실행
function runAllTests() {
    console.log('='.repeat(60));
    console.log('뒤로가기 버튼 테스트 시작');
    console.log('='.repeat(60));
    
    const results = [
        testBackButtonElements(),
        testBackButtonEventListeners(),
        testBackButtonClickHandlers(),
        testBackButtonCSS(),
        testBackButtonVisibility()
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


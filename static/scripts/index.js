const testTargetTime = new Date("2025-10-15T09:00:00+09:00");
const finalTestTargetTime = new Date("2025-11-13T08:40:00+09:00");

function updateTestCountdown() {
    const now = new Date();
    const testDiff = testTargetTime - now;

    if (testDiff <= 0) {
        document.getElementById('test_timer').textContent = "0일 0시간 0분 0초";
        return;
    }

    const days = String(Math.floor(testDiff / (1000 * 60 * 60 * 24)))
    const hours = String(Math.floor((testDiff % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60))).padStart(2, '0');
    const minutes = String(Math.floor((testDiff % (1000 * 60 * 60)) / (1000 * 60))).padStart(2, '0');
    const seconds = String(Math.floor((testDiff % (1000 * 60)) / 1000)).padStart(2, '0');

    document.getElementById('test_timer').textContent = `${days}일 ${hours}시간 ${minutes}분 ${seconds}초`;
}

function updateFinalTestCountdown() {
    const now = new Date();
    const finalTestDiff = finalTestTargetTime - now;

    if (finalTestDiff <= 0) {
        document.getElementById('final_test_timer').textContent = "0일 0시간 0분 0초";
        return;
    }

    const days = String(Math.floor(finalTestDiff / (1000 * 60 * 60 * 24)))
    const hours = String(Math.floor((finalTestDiff % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60))).padStart(2, '0');
    const minutes = String(Math.floor((finalTestDiff % (1000 * 60 * 60)) / (1000 * 60))).padStart(2, '0');
    const seconds = String(Math.floor((finalTestDiff % (1000 * 60)) / 1000)).padStart(2, '0');

    document.getElementById('final_test_timer').textContent = `${days}일 ${hours}시간 ${minutes}분 ${seconds}초`;
}

updateTestCountdown();
updateFinalTestCountdown();
setInterval(updateTestCountdown, 1000);
setInterval(updateFinalTestCountdown, 1000);
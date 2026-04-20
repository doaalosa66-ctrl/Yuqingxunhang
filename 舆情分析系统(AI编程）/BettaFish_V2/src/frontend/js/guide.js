(function(){
var STEPS = [0.75, 0.85, 1.0, 1.15, 1.3, 1.5];
var idx = 2;

window.guideZoom = function(dir) {
    if (dir === 0) { idx = 2; }
    else if (dir > 0 && idx < STEPS.length - 1) { idx++; }
    else if (dir < 0 && idx > 0) { idx--; }
    var c = document.getElementById('guideContent');
    var l = document.getElementById('guideZoomLabel');
    if (c) c.style.transform = 'scale(' + STEPS[idx] + ')';
    if (l) l.textContent = Math.round(STEPS[idx] * 100) + '%';
};

// 强制显示/隐藏函数
window.showGuide = function() {
    var overlay = document.getElementById('guideOverlay');
    var modal = document.getElementById('guideModal');
    if (overlay) {
        overlay.style.display = 'flex';
        overlay.style.opacity = '1';
        overlay.style.visibility = 'visible';
        overlay.style.pointerEvents = 'auto';
    }
    if (modal) {
        modal.style.transform = 'scale(1) translateY(0)';
    }
    document.body.style.overflow = 'hidden';
};

window.hideGuide = function() {
    var overlay = document.getElementById('guideOverlay');
    if (overlay) {
        overlay.style.display = 'none';
        overlay.style.opacity = '0';
        overlay.style.visibility = 'hidden';
        overlay.style.pointerEvents = 'none';
    }
    document.body.style.overflow = '';
};

// 绑定打开按钮
var guideTrigger = document.getElementById('guideTrigger');
if (guideTrigger) {
    guideTrigger.addEventListener('click', window.showGuide);
}

// 点击遮罩关闭
var overlay = document.getElementById('guideOverlay');
if (overlay) {
    overlay.addEventListener('click', function(e) {
        if (e.target === overlay) window.hideGuide();
    });
}

// ESC 关闭
document.addEventListener('keydown', function(e) {
    if (e.key === 'Escape') {
        window.hideGuide();
    }
});

// Ctrl+滚轮缩放
var modal = document.getElementById('guideModal');
if (modal) {
    modal.addEventListener('wheel', function(e) {
        if (!e.ctrlKey && !e.metaKey) return;
        e.preventDefault();
        window.guideZoom(e.deltaY < 0 ? 1 : -1);
    }, { passive: false });
}
})();

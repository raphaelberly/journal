// Close a full screen image by swiping it down, as in iOS apps: the image follows the finger while the dark
// background fades, then slides away past a threshold or on a flick, or else goes back into place
const SWIPE_DISTANCE = 100;  // px
const SWIPE_SPEED = 0.5;  // px/ms
const SWIPE_DURATION = 100;  // ms

let swipe = null;

// Move the images of the popover down by y, and fade its background accordingly
function moveSwipe(popover, y, animate) {
    const background = popover.querySelector('button');
    background.style.transition = animate ? `opacity ${SWIPE_DURATION}ms ease-out` : '';
    background.style.opacity = Math.max(0, 1 - 2 * y / window.innerHeight);
    for (const image of popover.querySelectorAll(':scope > img')) {
        image.style.transition = animate ? `transform ${SWIPE_DURATION}ms ease-out` : '';
        image.style.transform = `translateY(${y}px)`;
    }
}

document.addEventListener('touchstart', function (event) {
    const popover = event.target.closest('.fullscreen-image');
    if (popover && event.touches.length === 1) {
        swipe = {popover: popover, startY: event.touches[0].clientY, y: 0, time: event.timeStamp, speed: 0};
    }
});

document.addEventListener('touchmove', function (event) {
    if (!swipe) return;
    event.preventDefault();  // Keep the page from scrolling or bouncing under the image
    const y = Math.max(0, event.touches[0].clientY - swipe.startY);
    swipe.speed = (y - swipe.y) / Math.max(1, event.timeStamp - swipe.time);
    swipe.y = y;
    swipe.time = event.timeStamp;
    moveSwipe(swipe.popover, y, false);
}, {passive: false});

document.addEventListener('touchend', function (event) {
    if (!swipe) return;
    const {popover, y, speed} = swipe;
    swipe = null;
    if (y === 0) return;  // A tap, which the background button handles
    event.preventDefault();  // Keep the swipe from also counting as a tap on the background
    if (y > SWIPE_DISTANCE || speed > SWIPE_SPEED) {
        moveSwipe(popover, window.innerHeight, true);
        setTimeout(function () {
            popover.hidePopover();
            moveSwipe(popover, 0, false);
        }, SWIPE_DURATION);
    } else {
        moveSwipe(popover, 0, true);
    }
});

// Put the image back when the system takes the touch over
document.addEventListener('touchcancel', function () {
    if (!swipe) return;
    moveSwipe(swipe.popover, 0, true);
    swipe = null;
});

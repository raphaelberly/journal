// Show one slide at a time: a tap on the left third goes back, anywhere else goes forward, and past the last
// slide back to the first
let currentSlide = 0;

function showSlide(index) {
    const slides = document.querySelectorAll('.slide');
    currentSlide = (index + slides.length) % slides.length;
    slides.forEach((slide, i) => slide.classList.toggle('active', i === currentSlide));
    document.querySelectorAll('.progress span').forEach((bar, i) => bar.classList.toggle('done', i <= currentSlide));
    document.getElementById('chevron-left').style.visibility = currentSlide > 0 ? 'visible' : 'hidden';
    document.getElementById('chevron-right').style.visibility = currentSlide < slides.length - 1 ? 'visible' : 'hidden';
    slides[currentSlide].querySelectorAll('[data-count]').forEach(countUp);
}

// Count a number up from 0 to its value, slowing down towards the end
function countUp(element) {
    const target = parseFloat(element.dataset.count);
    const decimals = parseInt(element.dataset.decimals);
    const start = performance.now();
    function step(now) {
        const progress = Math.min((now - start) / 800, 1);
        const value = (target * (1 - Math.pow(1 - progress, 3))).toFixed(decimals);
        element.textContent = 'trimZero' in element.dataset ? value.replace('0.', '.') : value;
        if (progress < 1) {
            requestAnimationFrame(step);
        }
    }
    requestAnimationFrame(step);
}

document.addEventListener('DOMContentLoaded', () => {
    const story = document.getElementById('story');
    // Nothing logged this year: no story
    if (!story) {
        return;
    }
    // One progress segment per slide
    document.querySelectorAll('.slide').forEach(() => {
        document.getElementById('progress').appendChild(document.createElement('span'));
    });
    story.addEventListener('click', event => {
        showSlide(event.clientX < window.innerWidth / 3 ? Math.max(currentSlide - 1, 0) : currentSlide + 1);
    });
    document.addEventListener('keydown', event => {
        if (event.key === 'ArrowLeft') {
            showSlide(Math.max(currentSlide - 1, 0));
        } else if (event.key === 'ArrowRight') {
            showSlide(currentSlide + 1);
        }
    });
    showSlide(0);
});

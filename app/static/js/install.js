// Suggest adding Journal to the Home Screen, to phones browsing it in a tab, until the banner is closed
const INSTALL_SNOOZE = 30 * 24 * 3600 * 1000;  // ms
const RETRO_SNOOZE = 7 * 24 * 3600 * 1000;  // ms

// Tell whether a banner was closed less than snooze ago
function closedWithin(key, snooze) {
    try {
        return Date.now() - localStorage.getItem(key) < snooze;
    } catch (e) {
        return false;
    }
}

// Advertise the retrospective on the Search page while it is open, until the banner is closed
(function () {
    const banner = document.getElementById('retro');
    if (!banner || closedWithin('retroClosed', RETRO_SNOOZE)) return;
    banner.hidden = false;
    document.documentElement.style.setProperty('--install-height', `${banner.offsetHeight}px`);

    banner.addEventListener('click', function () {
        location.href = banner.dataset.href;
    });

    banner.querySelector('.install-close').addEventListener('click', function (event) {
        event.stopPropagation();
        banner.hidden = true;
        document.documentElement.style.setProperty('--install-height', '0px');
        try {
            localStorage.setItem('retroClosed', Date.now());
        } catch (e) {}
    });
})();

(function () {
    const banner = document.getElementById('install');
    if (!banner || navigator.standalone || matchMedia('(display-mode: standalone)').matches) return;
    if (closedWithin('installClosed', INSTALL_SNOOZE)) return;
    // Show one banner at a time: the retrospective one first, while it is open
    if ('retro' in banner.dataset && !closedWithin('retroClosed', RETRO_SNOOZE)) return;
    const button = banner.querySelector('.install-how');

    // Push the page down by the height of the banner, or put it back
    function show(visible) {
        banner.hidden = !visible;
        document.documentElement.style.setProperty('--install-height', `${banner.offsetHeight}px`);
    }

    banner.querySelector('.install-close').addEventListener('click', function () {
        show(false);
        try {
            localStorage.setItem('installClosed', Date.now());
        } catch (e) {}
    });

    // iPhone Safari: Add to Home Screen is a few taps away, whose path changed with Safari 26 and 27
    const safari = navigator.userAgent.match(/iPhone.*Version\/(\d+).*Safari/);
    if (safari) {
        const version = Number(safari[1]);
        banner.querySelector(version >= 26 ? '.ios18' : '.ios26').remove();
        banner.querySelector('.ios26 use')?.setAttribute('href', version >= 27 ? '#install-menu' : '#install-more');
        button.addEventListener('click', function () {
            button.textContent = banner.classList.toggle('open') ? 'Hide' : 'How?';
            show(true);
        });
        show(true);
    }

    // Android Chrome: open its own install dialog, once it tells the app can be installed
    window.addEventListener('beforeinstallprompt', function (event) {
        if (!/Android/.test(navigator.userAgent)) return;
        event.preventDefault();
        button.textContent = 'Install';
        button.addEventListener('click', function () {
            event.prompt();
            show(false);
        });
        show(true);
    });
})();

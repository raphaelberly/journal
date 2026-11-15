// Switch every date of the page between relative and absolute on a tap on any of them, and save the choice
document.addEventListener('click', function (event) {
    const tapped = event.target.closest('.date');
    if (!tapped) return;
    document.querySelectorAll('.date').forEach(function (date) {
        [date.textContent, date.dataset.alt] = [date.dataset.alt, date.textContent];
        date.classList.toggle('absolute');
    });
    fetch('/settings/dates', {method: 'POST', keepalive: true, body: new URLSearchParams({
        absolute_dates: tapped.classList.contains('absolute'),
        csrf_token: document.querySelector('meta[name="csrf-token"]').content,
    })});
});

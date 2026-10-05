// Invitation link of the settings page: hand it to the share sheet of the phone, or copy it where
// there is none

function shareInvite(button) {
    const url = new URL(button.dataset.url, location.href).href;
    if (!navigator.share) {
        copyInvite(button, url);
        return;
    }
    // Closing the share sheet rejects the promise too: only copy the link on another failure
    navigator.share({url: url}).catch(error => {
        if (error.name !== 'AbortError') copyInvite(button, url);
    });
}

function copyInvite(button, url) {
    navigator.clipboard.writeText(url).then(() => {
        // Keep the first label, should the button be tapped again within the 2 seconds
        button.dataset.label = button.dataset.label || button.textContent;
        button.textContent = 'Link copied';
        setTimeout(() => button.textContent = button.dataset.label, 2000);
    }, () => {
        // Clipboard refused (permissions): show the link, to copy by hand
        window.prompt('Copy this invitation link', url);
    });
}

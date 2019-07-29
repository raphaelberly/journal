function openAlert() {
    document.getElementsByClassName('alert hidden')[0].className = 'alert visible';
}

function closeAlert() {
    document.getElementsByClassName('alert visible')[0].className = 'alert hidden';
}

setTimeout(openAlert, 0);
setTimeout(closeAlert, 3500);

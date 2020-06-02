function openAlert() {
    element = document.getElementsByClassName('alert hidden')[0]
    element.className = element.className.replace('hidden', 'visible');
}

function closeAlert() {
    element = document.getElementsByClassName('alert visible')[0]
    element.className = element.className.replace('visible', 'hidden');
}

setTimeout(openAlert, 0);
setTimeout(closeAlert, 3500);

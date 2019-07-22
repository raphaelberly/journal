setTimeout(function(){
    document.getElementsByClassName('alert hidden')[0].className = 'alert visible';
}, 100);

setTimeout(function(){
    document.getElementsByClassName('alert visible')[0].className = 'alert hidden';
}, 4100);

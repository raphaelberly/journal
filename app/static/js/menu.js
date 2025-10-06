function openNav() {
    document.getElementById("mySidenav").style.right = "0";
    document.getElementById("sidenavback").style.transition = "background-color .2s linear 0s, z-index 0s linear 0s";
    document.getElementById("sidenavback").style.zIndex = "3";
    document.getElementById("sidenavback").style.backgroundColor = "rgba(0,0,0,0.3)";
}

function closeNav() {
    document.getElementById("mySidenav").style.right = "-250px";
    document.getElementById("sidenavback").style.transition = "background-color .2s linear 0s, z-index 0s linear .2s";
    document.getElementById("sidenavback").style.backgroundColor = "rgba(0,0,0,0.0)";
    document.getElementById("sidenavback").style.zIndex = "-1";
}

function topFunction() {
    document.body.scrollTop = 0; // For Safari
    document.documentElement.scrollTop = 0; // For Chrome, Firefox, IE and Opera
}

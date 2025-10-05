function openSubmenu() {
    document.getElementById("mySubmenu").style.bottom = "0px";
    document.getElementById("mySubmenuBack").style.transition = "background-color .2s linear 0s, z-index 0s linear 0s";
    document.getElementById("mySubmenuBack").style.zIndex = "3";
    document.getElementById("mySubmenuBack").style.backgroundColor = "rgba(0,0,0,0.3)";
}

function instantOpenSubmenu() {
    document.getElementById("mySubmenu").style.bottom = "0px";
    document.getElementById("mySubmenuBack").style.zIndex = "3";
    document.getElementById("mySubmenuBack").style.backgroundColor = "rgba(0,0,0,0.3)";
}

function closeSubmenu() {
    document.getElementById("mySubmenu").style.bottom = "-250px";
    document.getElementById("mySubmenuBack").style.transition = "background-color .2s linear 0s, z-index 0s linear .2s";
    document.getElementById("mySubmenuBack").style.backgroundColor = "rgba(0,0,0,0.0)";
    document.getElementById("mySubmenuBack").style.zIndex = "-1";
}

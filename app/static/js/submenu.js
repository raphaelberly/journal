function openSubmenu(submenuId) {
    document.getElementById(submenuId).style.bottom = "0px";
    document.getElementById(submenuId + "Back").style.transition = "background-color .2s linear 0s, z-index 0s linear 0s";
    document.getElementById(submenuId + "Back").style.zIndex = "3";
    document.getElementById(submenuId + "Back").style.backgroundColor = "rgba(0,0,0,0.3)";
}

function instantOpenSubmenu(submenuId) {
    document.getElementById(submenuId).style.bottom = "0px";
    document.getElementById(submenuId + "Back").style.zIndex = "3";
    document.getElementById(submenuId + "Back").style.backgroundColor = "rgba(0,0,0,0.3)";
}

function closeSubmenu(submenuId) {
    document.getElementById(submenuId).style.bottom = "-250px";
    document.getElementById(submenuId + "Back").style.transition = "background-color .2s linear 0s, z-index 0s linear .2s";
    document.getElementById(submenuId + "Back").style.backgroundColor = "rgba(0,0,0,0.0)";
    document.getElementById(submenuId + "Back").style.zIndex = "-1";
}

function setFieldHeight() {
    var navbarHeight = document.getElementById('navbar').offsetHeight;
    var guestBarHeight = 0;
    try {
        guestBarHeight = document.getElementById('guest_user_bar').offsetHeight;
    } catch {
    }
    document.getElementById('field').setAttribute("style","height: calc(100vh - " + (navbarHeight + guestBarHeight) + "px)");
}

window.onload = function() {
    setFieldHeight();
};  

document.querySelector("#casecooler_button").addEventListener("click", event => {
    x = document.getElementById('casecooler_panel');
    if (x.style.display === 'none') {
        x.style.display = 'flex';
      } else {
        x.style.display = 'none';
      }
});

document.querySelector("#motherboard_button").addEventListener("mouseover", event => {
    if(document.getElementById("motherboard").className === "component_light"){
        document.getElementById("motherboard").className = "component_light_hovered";
    } else {
        document.getElementById("motherboard").className = "component_dark_hovered";
    }
    if(document.getElementById("motherboard_button").className === "component_add_button_light"){
        document.getElementById("motherboard_button").className = "component_add_button_light_hovered";
    } else {
        document.getElementById("motherboard_button").className = "component_add_button_dark_hovered";
    }
});

document.querySelector("#motherboard_button").addEventListener("mouseout", event => {
    if(document.getElementById("motherboard").className === "component_light_hovered"){
        document.getElementById("motherboard").className = "component_light";
    } else {
        document.getElementById("motherboard").className = "component_dark";
    }
    if(document.getElementById("motherboard_button").className === "component_add_button_light_hovered"){
        document.getElementById("motherboard_button").className = "component_add_button_light";
    } else {
        document.getElementById("motherboard_button").className = "component_add_button_dark";
    }
});
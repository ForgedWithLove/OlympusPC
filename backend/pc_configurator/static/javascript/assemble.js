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

var processor_name = document.getElementById('processor_name');
if (typeof(processor_name) != 'undefined' && processor_name != null)
{
    processor_name.addEventListener("mouseover", event => {
        x = document.getElementById('processor_info');
        x.style.display = 'block';
    });
    processor_name.addEventListener("mouseout", event => {
        x = document.getElementById('processor_info');
        x.style.display = 'none';
    });
}

var motherboard_name = document.getElementById('motherboard_name');
if (typeof(motherboard_name) != 'undefined' && motherboard_name != null)
{
    motherboard_name.addEventListener("mouseover", event => {
        x = document.getElementById('motherboard_info');
        x.style.display = 'block';
    });
    motherboard_name.addEventListener("mouseout", event => {
        x = document.getElementById('motherboard_info');
        x.style.display = 'none';
    });
}

var videocard_name = document.getElementById('videocard_name');
if (typeof(videocard_name) != 'undefined' && videocard_name != null)
{
    videocard_name.addEventListener("mouseover", event => {
        x = document.getElementById('videocard_info');
        x.style.display = 'block';
    });
    videocard_name.addEventListener("mouseout", event => {
        x = document.getElementById('videocard_info');
        x.style.display = 'none';
    });
}

var memory_name = document.getElementById('memory_name');
if (typeof(memory_name) != 'undefined' && memory_name != null)
{
    memory_name.addEventListener("mouseover", event => {
        x = document.getElementById('memory_info');
        x.style.display = 'block';
    });
    memory_name.addEventListener("mouseout", event => {
        x = document.getElementById('memory_info');
        x.style.display = 'none';
    });
}

var cooler_name = document.getElementById('cooler_name');
if (typeof(cooler_name) != 'undefined' && cooler_name != null)
{
    cooler_name.addEventListener("mouseover", event => {
        x = document.getElementById('cooler_info');
        x.style.display = 'block';
    });
    cooler_name.addEventListener("mouseout", event => {
        x = document.getElementById('cooler_info');
        x.style.display = 'none';
    });
}

var case_name = document.getElementById('case_name');
if (typeof(case_name) != 'undefined' && case_name != null)
{
    case_name.addEventListener("mouseover", event => {
        x = document.getElementById('case_info');
        x.style.display = 'block';
    });
    case_name.addEventListener("mouseout", event => {
        x = document.getElementById('case_info');
        x.style.display = 'none';
    });
}

var powersupply_name = document.getElementById('powersupply_name');
if (typeof(powersupply_name) != 'undefined' && powersupply_name != null)
{
    powersupply_name.addEventListener("mouseover", event => {
        x = document.getElementById('powersupply_info');
        x.style.display = 'block';
    });
    powersupply_name.addEventListener("mouseout", event => {
        x = document.getElementById('powersupply_info');
        x.style.display = 'none';
    });
}

var disc_names = document.querySelectorAll('.disc_selected_name');
if (typeof(disc_names) != 'undefined' && disc_names != null)
{
    for (let i = 0; i < disc_names.length; i++) {
        disc_names[i].addEventListener("mouseover", event => {
            x = document.getElementById('discs_info');
            x.style.display = 'block';
        });
        disc_names[i].addEventListener("mouseout", event => {
            x = document.getElementById('discs_info');
            x.style.display = 'none';
        });
    }
}

var casecooler_button = document.getElementById('casecooler_button');
if (typeof(casecooler_button) != 'undefined' && casecooler_button != null)
{
    casecooler_button.addEventListener("click", event => {
        x = document.getElementById('casecooler_side_container');
        if (x.style.display === 'none') {
            x.style.display = 'flex';
          } else {
            x.style.display = 'none';
          }
    });
}

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
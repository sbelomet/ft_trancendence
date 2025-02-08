document.addEventListener("DOMContentLoaded",() => {
    const content = document.getElementById("start_point");
    content.setAttribute("class", "d-flex justify-content-center");

    const button = document.createElement("button");
    button.id = "button_websocket";
    button.textContent = "click here";
    button.type = "button";
    button.setAttribute("class", "btn btn-success");
    button.addEventListener("click", () => {
        window.alert("HAHAAAAAAAA!");
    })
    content.appendChild(button);
})
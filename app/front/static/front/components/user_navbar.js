import managerState from "../classes/ManagerState.js";
import { user_dropdown } from "../utils/components_utils.js";

const user_navbar = () => {
    const data = managerState.getUser;

    const parentNode = document.getElementById("user_navbar");
    while (parentNode.lastElementChild) {
        parentNode.removeChild(parentNode.lastElementChild);
    };

    if (data) {

        const image = document.createElement("img");
        image.src = data.avatar;
        image.setAttribute("class", "align-self-center rounded");
        image.alt = "user avatar";
        image.width = "30";
        image.height = "26";
        parentNode.appendChild(image);

        const ul = document.createElement("ul");
        ul.setAttribute("class", "nav nav-pills");

        const li_dropdown = document.createElement("li");
        li_dropdown.setAttribute("class", "nav-item dropdown");

        const anchor = document.createElement("a");
        anchor.setAttribute("class", "nav-link dropdown-toggle me-5");
        anchor.setAttribute("data-bs-toggle", "dropdown");
        anchor.role = "button";
        anchor.ariaExpanded = false;
        anchor.textContent = data.username;
        li_dropdown.appendChild(anchor);

        const sub_ul = document.createElement("ul");
        sub_ul.setAttribute("class", "dropdown-menu");

        const dropdown_elements = user_dropdown(data.id);
        for (const item of dropdown_elements) {
            const li = document.createElement("li");

            const anchor = document.createElement("a");
            anchor.setAttribute("class", item.class);
            anchor.role = "button";
            anchor.textContent = item.content;

            anchor.addEventListener("click", () => {
                managerState.loadFragmentPage(item.path)
            });

            li.appendChild(anchor);
            sub_ul.appendChild(anchor);
        }

        const li_dropitem = document.createElement("li");
        const divider = document.createElement("hr");
        divider.setAttribute("class", "dropdown-divider");
        li_dropitem.appendChild(divider);
        sub_ul.appendChild(li_dropitem);
    
        const wrapper = document.createElement("div");
        wrapper.setAttribute("class", "text-center m-0 p-0");

        const button = document.createElement("button");
        button.setAttribute("class", "btn btn-danger btn-sm");
        button.type = "button";
        button.textContent = "Logout";
        button.addEventListener("click", managerState.logout.bind(managerState));
        wrapper.appendChild(button);
        sub_ul.appendChild(wrapper);
    
        li_dropdown.appendChild(sub_ul);
        ul.appendChild(li_dropdown);
        parentNode.appendChild(ul);
    } else {
        const div = document.createElement("div");
        div.setAttribute("class", "h-100 d-flex align-items-center");

        const p = document.createElement("p");
        p.textContent = "Guest";
        p.setAttribute("class", "text-light m-0 p-2");

        div.appendChild(p)
        parentNode.appendChild(div);
    }
}

export default user_navbar;
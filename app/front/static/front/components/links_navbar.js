import managerState from "../classes/ManagerState.js";
import { links_elements } from "../utils/components_utils.js";

const links_navbar = () => {
    const user = managerState.getLogged;

    const parentNode = document.getElementById("links_navbar");
    while (parentNode.lastElementChild) {
        parentNode.removeChild(parentNode.lastElementChild);
    };

    for (const [index, item] of links_elements.entries()) {
        if (!user && (index === 2)) {
            continue ;
        } else if (user && (index === 3)) {
            break ;
        }

        const li = document.createElement("li");
        li.setAttribute("class", item.li_class);

        const anchor = document.createElement("a");
        anchor.setAttribute("class", item.anchor.class);
        anchor.role = "button";
        anchor.textContent = item.anchor.content;

        anchor.addEventListener("click", () => {
            managerState.loadFragmentPage(item.anchor.path);
        });

        li.appendChild(anchor);
        parentNode.appendChild(li);
    }
}

export default links_navbar;
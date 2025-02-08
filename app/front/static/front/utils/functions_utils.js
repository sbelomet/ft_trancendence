import { endpoints } from "../utils/utils.js";
import { GET } from "../api.js";
import { setChatLinksInert } from "../handle_chat.js";

function formatDateTime(dateString) {
    if (!dateString) return "Unknown Date";

    const date = new Date(dateString);

    // Construire la date au format DD/MM/YY
    const day = String(date.getDate()).padStart(2, '0');
    const month = String(date.getMonth() + 1).padStart(2, '0'); // Les mois commencent à 0
    const year = String(date.getFullYear()).slice(-2); // Obtenir les deux derniers chiffres de l'année

    // Construire l'heure sans les secondes
    const hours = String(date.getHours()).padStart(2, '0');
    const minutes = String(date.getMinutes()).padStart(2, '0');

    return `${day}/${month}/${year} ${hours}:${minutes}`;
};

/**
 * @param {HTMLElement} element 
 * @returns {Object}
*/
function canvasSize(element) {
    return ({
        width: element.clientWidth,
        height: element.clientHeight,
    })
}

async function getUserInfo(userId) {
    const userInfo = await GET(endpoints.userDetails(userId));
    if (userInfo.ok) {
        return (userInfo.data);
    } else 
        return (undefined);
};

function inertNavbarFooter(toInert = false) {
    const header = document.getElementById("header_content");
    const footerSearch = document.getElementById("footer_search");

    if (toInert) {
        header.setAttribute("inert", "");
        footerSearch.setAttribute("inert", "");
    } else {
        header.removeAttribute("inert");
        footerSearch.removeAttribute("inert");
    }
	setChatLinksInert(toInert);
}

export { inertNavbarFooter, formatDateTime, canvasSize, getUserInfo };
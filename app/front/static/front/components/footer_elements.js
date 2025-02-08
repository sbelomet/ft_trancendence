import managerState from "../classes/ManagerState.js";

const footer_elements = () => {
    const user = managerState.getLogged;

    const chatParentNode = document.getElementById("footer_chat");
	const searchParentNode = document.getElementById("footer_search");

	while (chatParentNode.lastElementChild) {
        chatParentNode.removeChild(chatParentNode.lastElementChild);
	};
	while (searchParentNode.lastElementChild) {
        searchParentNode.removeChild(searchParentNode.lastElementChild);
    };

    if (user) {
		// Chat button
        const button = document.createElement("button");
        button.type = "button";
        button.textContent = "Open chat";
		button.setAttribute("id", "open-chat-btn");
        button.setAttribute("data-bs-toggle", "offcanvas");
        button.setAttribute("aria-controls", "offcanvasChat");
        button.setAttribute("data-bs-target", "#offcanvasChat");
        button.setAttribute("class", "btn btn-primary btn-lg my-2");

		// Notification badge
		const badge = document.createElement("span");
		badge.setAttribute("id", "openchat-notification-badge");
		badge.setAttribute("class", "position-absolute badge rounded-pill bg-danger");
		badge.setAttribute(
			"style",
			"display: none; width: 15px; height: 15px; padding: 0; transform: translate(35%, 30%);"
		);

		button.appendChild(badge);
        chatParentNode.appendChild(button);

		managerState.loadChatModal();

        const searchInput = document.createElement("input");
        searchInput.type = "text";
        searchInput.placeholder = "Search users...";
        searchInput.setAttribute("class", "form-control");
        searchInput.setAttribute("id", "user-search-input");

        const searchResults = document.createElement("ul");
        searchResults.style = "width: 15rem;";
        searchResults.setAttribute("id", "search-results");
        searchResults.setAttribute(
            "class",
            "list-group position-absolute bg-light ms-2"
        );
        searchResults.style.zIndex = "1040";

        searchParentNode.appendChild(searchInput);
        searchParentNode.appendChild(searchResults);

        searchInput.addEventListener("input", () => managerState.searchUsers());
    } 
	else {
        chatParentNode.classList.add("fill_footer");
        const chatModal = document.getElementById("chat_modal_special");
        while (chatModal.lastElementChild) {
            chatModal.removeChild(chatModal.lastElementChild);
        };
    }
}

export default footer_elements;
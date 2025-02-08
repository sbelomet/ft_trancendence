import { history_state } from "./utils/utils.js";
import managerState from "./classes/ManagerState.js";
import managerToast from "./classes/ManagerToast.js";

document.addEventListener("DOMContentLoaded", async () => {
    await managerState.self();
    managerToast.init();
    managerState.populate();
    if (managerState.getLoaded) {
        const path = window.location.pathname;
        managerState.reloadJsFile(path);
        managerState.listeningAnchors();
    }
});

window.addEventListener("popstate", (e) => {
    const path = window.location.pathname;
    //console.log("popstate to path: ", path);
    if (path === "/") {
        //console.log("home");
        e.preventDefault();
        window.history.replaceState("", "", "/");
        managerState.loadFragmentPage("/", false);
    } else {
        //console.log("no home");
        e.preventDefault();
        managerState.loadFragmentPage(path, history_state.nopush);
    }
});
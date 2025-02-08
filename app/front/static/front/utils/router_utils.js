import Profile from "../classes/Profile.js";
import HubPage from "../classes/HubPage.js";
import OTPForm from "../classes/OTPForm.js";
import LoginForm from "../classes/LoginForm.js";
import GameRender from "../classes/GameRender.js";
import SettingsPage from "../classes/SettingsPage.js";
import RegisterForm from "../classes/RegisterForm.js";
import OAuthLoginForm from "../classes/OAuthLoginForm.js"

import { chatEntrypoint } from "../handle_chat.js";
import { getUserInfo, inertNavbarFooter } from "./functions_utils.js";
import { colorToast, currentProfile, endpoints, history_state } from "./utils.js";

import managerState from "../classes/ManagerState.js";
import managerToasts from "../classes/ManagerToast.js";

async function initGame() {
    let game = new GameRender();

    game.addEventListener("toasts", (e) => {
        managerToasts.makeToast({
            message: e.message,
            clickable: false,
            toast_color: colorToast.blue
        });
    });
    game.addEventListener("error", () => {
        game = null;
        inertNavbarFooter();
        managerState.loadFragmentPage(endpoints.hub, history_state.replace);
    });
    game.addEventListener("close", () => {
        if (!game.getInTournament) {
            game = null;
            setTimeout(() => {
                managerState.loadFragmentPage(endpoints.hub, history_state.replace);
            }, 2000);
        } else
            game = null;
        inertNavbarFooter();
    });

    await game.init();
    inertNavbarFooter(true);
    game.startGame();
}

async function initHub() {
    if (!managerState.getUser) {
        managerToasts.makeToast({
            message: "You are not logged",
            clickable: false,
            toast_color: colorToast.red
        });
    } else {
        const hubPage = new HubPage();
        await hubPage.init();
    }
}

function initOTP() {
    const element = document.getElementById("otp_form");
    new OTPForm(element);
}

function initSettings() {
    const element = document.getElementById("settings_form");
    new SettingsPage(element);
}

async function initProfile(id) {
    if (!managerState.getUser || !(await getUserInfo(id))) {
        managerToasts.makeToast({
            message: !(id === undefined) ? "This user doesn't exist"
                : !(managerState.getUser) ? "You are not logged" : "",
            clickable: false,
            toast_color: colorToast.red
        });
    } else {
        currentProfile.id = id;
        if (currentProfile.current !== undefined)
            currentProfile.current.destroy();
        currentProfile.current = new Profile(id);
        await currentProfile.current.init();
    }
}
 
function initRegister() {
    const element = document.getElementById("register_form");
    new RegisterForm(element);
}

function initLogin() {
    const element = document.getElementById("login_form");
    new LoginForm(element);
}

function initOAuth() {
    const element = document.getElementById("oauth_form");
    new OAuthLoginForm(element);
}

function initChat() {
	chatEntrypoint();
}

const routes_template =  Object.freeze({
    "/otp/?method_2fa=totp": initOTP,
    "/otp/?method_2fa=email": initOTP,
    "/hub/": initHub,
    "/game/": initGame,
    "/login/": initLogin,
    "/chat_modal/": initChat,
    "/register/": initRegister,
    "/settings/": initSettings,
	"/oauth_login/": initOAuth
});

const route_profiles = (id) => {
    initProfile(id); 
}

export { routes_template, route_profiles };
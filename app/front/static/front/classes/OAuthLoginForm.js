import managerState from "./ManagerState.js";

export default class OAuthLoginForm {
    form = null;

    constructor(form) {
        this.form = form;
        this.form.addEventListener("submit", async (e) => {
            e.preventDefault();
            e.stopPropagation();
            if (this.validate()) {
                managerState.initiateOAuthLogin();
				return;
            }
        });
	}

    /* Getters - Setters */

    get getForm() {
        return this.form;
    }

    /**
     * @param {HTMLFormElement} form
     */
    set setForm(form) {
        this.form = form;
    }

    /* Methods */

    validate() {
        // For OAuth, validation may check if the form element exists
        if (this.form) {
            return true;
        }
        return false;
    }

   /*  async redirectToOAuth() {
        try {
            const response = await managerState.initiateOAuthLogin();
            if (response.redirect_url) {
                window.location.href = response.redirect_url;
            } else {
                console.error("No redirect URL received from server.");
            }
        } catch (error) {
            console.error("Error redirecting to OAuth login:", error);
        }
    } */
}


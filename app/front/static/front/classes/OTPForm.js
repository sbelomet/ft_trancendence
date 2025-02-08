import managerState from "./ManagerState.js";
import managerStatus from "./ManagerStatus.js";
import managerToast from "./ManagerToast.js";
import {colorToast, endpoints}from "../utils/utils.js";


export default class OTPForm {
    form = null;
	username = "";
    code = "";

	constructor(form) {
		this.form = form;
		this.init();
		this.form.addEventListener("submit", async (e) => {
			e.preventDefault();
			e.stopPropagation();
			if (this.validate()) {
				const toSend = { code: this.code };
	
				managerState.otp(toSend);
			}
		});

    }
	

    /* Getters - Setters */

    get getForm() {
        return (this.form);
    }

    get getCode() {
        return (this.code);
    }


    /**
     * @param {HTMLFormElement} form
    */
    set setForm(form) {
        this.form = form;
    }

    /**
     * @param {string} value
    */
    set setCode(value) {
        this.code = value;
    }

    /* Methods */

	async init() {
		const method2FA = this.getQueryParam("method_2fa"); 
	
		if (method2FA === "totp") {
			const emailLinkContainer = document.createElement("div");
			emailLinkContainer.className = "text-center mt-3";
			emailLinkContainer.innerHTML = `
				If you prefer to get your code by email, <a href="#" id="request_email_otp">click here</a>.
			`;
			const dynamicContainer = this.form.querySelector("#dynamic_2fa_message");
			dynamicContainer.appendChild(emailLinkContainer);
	
			const emailLink = document.getElementById("request_email_otp");
			emailLink.addEventListener("click", async (e) => {
				e.preventDefault();
				await this.requestEmailOtp();
			});
		}
		if (method2FA === "email") { 
			managerToast.makeToast({
				message: `Access code sent to your email. It expires in 60 seconds.`,
				clickable: false,
				toast_color: colorToast.blue
			});
		}
	}

	getQueryParam(param) {
		const urlParams = new URLSearchParams(window.location.search);
		return urlParams.get(param);
	}
	

	async requestEmailOtp() {
		const response = await fetch(endpoints.otp, {
			method: "POST",
			headers: {
				"Content-Type": "application/json",
				"X-CSRFToken": this.getCsrfToken(),
			},
			body: JSON.stringify({ "2fa_method": "email" }),
		});

		if (!response.ok) {
			managerStatus.handleErrorResponse(response.status, response.data, false);
			return;
		}
		
		managerToast.makeToast({
            message: `Access code sent to your email. It expires in 60 seconds.`,
            clickable: false,
            toast_color: colorToast.blue
        });
		
	}
	

    getCsrfToken() {
        return document.querySelector("[name=csrfmiddlewaretoken]").value;
    }


    validate() {
        const code = document.getElementById("input_code").value;
        if (code !== "") {
            this.code = code
            this.resetInputs();
            return (true);
        }
        return (false);
    }

    resetInputs() {
        document.getElementById("input_code").value = "";
    }
}
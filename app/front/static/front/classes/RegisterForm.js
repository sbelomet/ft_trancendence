import managerState from "./ManagerState.js";
import managerToast from "./ManagerToast.js";
import { colorToast, select_auth } from "../utils/utils.js";

export default class RegisterForm {
    form = null;
    email = "";
    avatar = "";
    password = "";
    username = "";
    authValue = select_auth.none;
    confirmPassword = "";

    constructor (form) {
        this.form = form;
        this.init();
        this.form.addEventListener("submit", async (e) => {
            e.preventDefault();
            e.stopPropagation();
            if (this.validate()) {
                const toSend = {
                    email: this.email,
                    username: this.username,
                    password: this.password,
                    enable_2fa: this.authValue,
                };
                // Add avatar if selected
                if (this.avatar !== "") {
                    toSend.avatar = this.avatar; // Keep the `File` object for FormData processing
                }

                managerState.register( toSend );
                //document.cookie = "csrftoken=; expires=Thu, 01 Jan 1970 00:00:00 UTC";
                return ;
			}
        });
        document.getElementById("input_email").addEventListener("keyup", this.validateEmail.bind(this));
        document.getElementById("input_avatar").addEventListener("change", this.validateAvatar.bind(this));
        document.getElementById("input_username").addEventListener("keyup", this.validateUsername.bind(this));
        document.getElementById("input_password").addEventListener("keyup", this.validatePassword.bind(this));
        document.getElementById("select_auth").addEventListener("change", this.getSelectValue.bind(this));
        
    }

    /* Getters - Setters */

    get getForm() {
        return (this.form);
    }

    get getEmail() {
        return (this.email);
    }

    get getAvatar() {
        return (this.avatar);
    }

    get getUsername() {
        return (this.username);
    }

    get getPassword() {
        return (this.password);
    }

    /**
     * @param {HTMLFormElement} form
    */
    set setForm(form) {
        this.form = form;
    }

    /**
     * @param {string} email
     */
    set setEmail(email) {
        this.email = email;
    }

    /**
     * @param {string} avatar
    */
    set setAvatar(avatar) {
        this.avatar = avatar;
    }

    /**
     * @param {string} password
    */
    set setPassword(password) {
        this.password = password;
    }

    /**
     * @param {string} username
    */
    set setUsername(username) {
        this.username = username;
    }

    /* Methods */

    async init() {
		const error = this.getQueryParam("error"); 
	
		if (error) { 
            managerToast.makeToast({
                message: error,
                clickable: false,
                toast_color: colorToast.red
            });
		}
	}

	getQueryParam(param) {
		const urlParams = new URLSearchParams(window.location.search);
		return urlParams.get(param);
	}

    validate() {
        if (this.email !== "" && 
            this.password !== "" &&
            this.username !== "" &&
            this.validateEmail() &&
            this.validatePassword()
        ) {
            
            if (!this.validateAvatar()) {
                return false;
            }
            if (this.password !== this.confirmPassword){
                managerToast.makeToast({
                    message: "Passwords do not match!",
                    clickable: false,
                    toast_color: colorToast.blue
                });
                return false;
            }
            return true;
        }
        return false;
    }

    getSelectValue() {
        const selectAuth = document.getElementById("select_auth");
        switch (selectAuth.value) {
            case "Application":
                this.authValue = select_auth.application;
                break;
            case "None":
                this.authValue = select_auth.none;
                break;
            case "Email":
                this.authValue = select_auth.email;
                break;
            default:
                this.authValue = select_auth.none;
                break;
        }
    }

    validateAvatar() {
		const avatarInput = document.getElementById("input_avatar");
		const avatarError = document.getElementById("avatar_error");
		avatarError.innerText = "";
		avatarError.classList.add("d-none");
	
		if (!avatarInput.files || avatarInput.files.length === 0) {
			this.avatar = ""; // No avatar selected; backend will assign default
			avatarInput.classList.remove("is-invalid");
			return true;
		}
	
		const file = avatarInput.files[0];
		const allowedTypes = ["image/jpeg", "image/png", "image/jpg"];
		const maxSize = 2 * 1024 * 1024; // 2 MB
	
		// Validate file type
		if (!allowedTypes.includes(file.type)) {
			avatarError.innerText = "Invalid file type. Please upload a JPEG, JPG or PNG image.";
			avatarError.classList.remove("d-none");
			avatarInput.classList.add("is-invalid");
			this.avatar = ""; // Reset avatar
			return false;
		}
	
		// Validate file size
		if (file.size > maxSize) {
			avatarError.innerText = "File size exceeds 2 MB. Please upload a smaller image.";
			avatarError.classList.remove("d-none");
			avatarInput.classList.add("is-invalid");
			this.avatar = ""; // Reset avatar
			return false;
		}
	
		// If validation passes
		avatarInput.classList.remove("is-invalid");
		this.avatar = file; // Store the file for further use
		avatarError.classList.add("d-none");
		return true;
	}
	

    validatePassword() {
        const password = document.getElementById("input_password");
        this.confirmPassword = document.getElementById("input_confirm_password").value;
        password.classList.remove("is-invalid");
        if (password.value.trim() === "") {
            password.classList.add("is-invalid");
            return false;
        }
        const validationRegex = [
            { regex: /.{8,}/ }, // min 8 letters,
            { regex: /[0-9]/ }, // numbers from 0 - 9
            { regex: /[a-z]/ }, // letters from a - z (lowercase)
            { regex: /[A-Z]/ }, // letters from A-Z (uppercase),
            { regex: /[^A-Za-z0-9]/} // special characters
        ]
        for (const item of validationRegex) {
            if (!password.value.match(item.regex)) {
                password.classList.add("is-invalid");
                return false;
            }
        }
        this.password = password.value;
        password.classList.remove("is-invalid");
        return true;
    }

    validateUsername() {
        const username_error = document.getElementById("username_error");
        username_error.innerText = "";
        username_error.classList.add("d-none");

        const username = document.getElementById("input_username").value;
        // Make post check if username already in use?
        if (username.trim() === "") {
            username_error.innerText = "Username field is empty";
            username_error.classList.remove("d-none");
        }
        else {
            this.username = username;
            username_error.innerText = "";
            username_error.classList.add("d-none");
        }
    }

    validateEmail() {
        const email_error = document.getElementById("email_error");
        email_error.innerText = "";
        email_error.classList.add("d-none");

        const email = document.getElementById("input_email").value;
        const regEmail = /^(([^<>()[\]\\.,;:\s@"]+(\.[^<>()[\]\\.,;:\s@"]+)*)|.(".+"))@((\[[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\])|(([a-zA-Z\-0-9]+\.)+[a-zA-Z]{2,}))$/;
        if (email.trim() === "") {
            email_error.innerText = "Email field is empty";
            email_error.classList.remove("d-none");
        }
        else if (!email.toLowerCase().match(regEmail)) {
            email_error.innerText = "Email format error";
            email_error.classList.remove("d-none");
        }
        else {
            this.email = email;
            email_error.innerText = "";
            email_error.classList.add("d-none");
            return true;
        }
        return false;
    }

    resetInputs() {
        this.form.reset();
    }

}
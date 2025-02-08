import managerState from "./ManagerState.js";
import managerToast from "./ManagerToast.js";
import { colorToast } from "../utils/utils.js";
import { getUserInfo } from "../utils/functions_utils.js";


export default class SettingsPage {
    form = null;
    email = "";
    avatar = "";
    password = "";
    confirmPassword = "";
    username = "";
    nickname = "";
    authValue = "none";
	user = false

    constructor(form) {
		
        this.form = form;
        this.initializeSettings()
        this.form.addEventListener("submit", async (e) => {
			e.preventDefault();
            e.stopPropagation();
			this.updateValuesFromInputs();
            if (this.user && this.validate()) {
				const toSend = {
					email: this.email,
					username: this.username,
					password: this.password,
					enable_2fa: this.authValue,
					avatar: this.avatar || undefined, // Include avatar only if provided
                    nickname: this.nickname,
                };

                managerState.settings(toSend);
				return;
            } else {
                if (!this.user) {
                    managerToast.makeToast({
                        message: "You have to login to change settings!",
                        clickable: false,
                        toast_color: colorToast.blue
                    });
                    return;
                }
				managerToast.makeToast({
                    message: "Inputs are not valid.",
                    clickable: false,
                    toast_color: colorToast.blue
                });
			}
        });

        document.getElementById("input_email").addEventListener("keyup", this.validateEmail.bind(this));
        document.getElementById("input_password").addEventListener("keyup", this.validatePassword.bind(this));
        document.getElementById("input_avatar").addEventListener("change", this.validateAvatar.bind(this));
    }

    /* Getters and Setters */

    get getEmail() {
        return this.email;
    }

    get getAvatar() {
        return this.avatar;
    }

    get getPassword() {
        return this.password;
    }

    get getConfirmPassword() {
        return this.confirmPassword;
    }

    get getUsername() {
        return this.username;
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
     * @param {string} confirmPassword
    */
    set setConfirmPassword(confirmPassword) {
        this.confirmPassword = confirmPassword;
    }

    /**
     * @param {string} username
    */
    set setUsername(username) {
        this.username = username;
    }

    async initializeSettings() {
        try {
            const user = managerState.getUser;
            if (user) {
				this.user = true;
                await this.populateFields(user);
            } else {
                // alert("Failed to load user data. Please try refreshing the page.");
                managerToast.makeToast({
                    message: "Failed to load user data.",
                    clickable: false,
                    toast_color: colorToast.blue
                });
            }
        } catch (error) {
            console.error("Error loading user settings:", error);
            // alert("Unable to load settings. Please try again.");
            managerToast.makeToast({
                message: "Unable to load settings. Please try again.",
                clickable: false,
                toast_color: colorToast.red
            });
        }
    }

	async populateFields(user) {
        const usernameInput = document.getElementById("input_username");
        const nicknameInput = document.getElementById("input_nickname");
        const emailInput = document.getElementById("input_email");
        const authSelect = document.getElementById("select_auth");

        const userInfo = await getUserInfo(user.id)
            
        user.nickname = userInfo.nickname;

        usernameInput.placeholder = user.username || "Enter new username";
        nicknameInput.placeholder = user.nickname || "Enter new nickname";
        emailInput.placeholder = user.email || "Enter new email";
        if (authSelect) {
            authSelect.value = user.enable_2fa || "none";
        }

        // Set initial values to compare against changes later
        this.username = user.username;
        this.nickname = user.nickname;
        this.email = user.email;
        this.authValue = user.enable_2fa;
    }

	updateValuesFromInputs() {
		const emailInput = document.getElementById("input_email");
		const usernameInput = document.getElementById("input_username");
		const passwordInput = document.getElementById("input_password");
		const confirmPasswordInput = document.getElementById("input_confirm_password");
		const authSelect = document.getElementById("select_auth");
		const avatarInput = document.getElementById("input_avatar");
        const nicknameInput = document.getElementById("input_nickname");
	
		this.email = emailInput?.value.trim() || "";
		this.username = usernameInput?.value.trim() || "";
        this.nickname = nicknameInput?.value.trim() || "";
		this.password = passwordInput?.value || "";
		this.confirmPassword = confirmPasswordInput?.value || "";
		this.authValue = authSelect?.value || "none";
		this.avatar = avatarInput?.files[0] || "";
	}

    /* validate() {
        const emailValid = this.getEmail === "" || this.validateEmail();
        const passwordValid = this.getPassword === "" || (this.validatePassword() && this.getPassword === this.getConfirmPassword);
        const usernameValid = this.getUsername === "" || this.validateUsername();

        if (emailValid && passwordValid && usernameValid) {
            return true;
        }
        alert("Please check your inputs and try again.");
        return false;
    } */
	validate() {
        let isValid = true;

        if (this.email !== "") {
            isValid = this.validateEmail() && isValid;
        }
        if (this.password !== "") {
            isValid = this.validatePassword() && (this.password === this.confirmPassword) && isValid;
            if (this.password !== this.confirmPassword){
                // alert("Passwords do not match!");
                managerToast.makeToast({
                    message: "Passwords do not match!",
                    clickable: false,
                    toast_color: colorToast.blue
                });
            }
        }
        if (this.avatar !== "") {
            isValid = this.validateAvatar() && isValid;
        }

        return isValid;
    }

   /*  getSelectValue() {
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
    } */

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

        if (!allowedTypes.includes(file.type)) {
            avatarError.innerText = "Invalid file type. Please upload a JPEG, JPG. or PNG image.";
            avatarError.classList.remove("d-none");
            avatarInput.classList.add("is-invalid");
            this.avatar = "";
            return false;
        }

        if (file.size > maxSize) {
            avatarError.innerText = "File size exceeds 2 MB. Please upload a smaller image.";
            avatarError.classList.remove("d-none");
            avatarInput.classList.add("is-invalid");
            this.avatar = "";
            return false;
        }

        avatarInput.classList.remove("is-invalid");
        this.avatar = file;
        avatarError.classList.add("d-none");
        return true;
    }

    validatePassword() {
        const passwordInput = document.getElementById("input_password");
        const passwordError = document.getElementById("password_error");
        passwordInput.classList.remove("is-invalid");
        passwordError.innerText = "";
        passwordError.classList.add("d-none");

        const validationRegex = [
            { regex: /.{8,}/, message: "Minimum 8 characters." },
            { regex: /[0-9]/, message: "At least one number." },
            { regex: /[a-z]/, message: "At least one lowercase letter." },
            { regex: /[A-Z]/, message: "At least one uppercase letter." },
            { regex: /[^A-Za-z0-9]/, message: "At least one special character." },
        ];

        for (const rule of validationRegex) {
            if (!passwordInput.value.match(rule.regex)) {
                passwordError.innerText = rule.message;
                passwordError.classList.remove("d-none");
                passwordInput.classList.add("is-invalid");
                return false;
            }
        }

        this.password = passwordInput.value;
        return true;
    }

    /* validateConfirmPassword() {
        const confirmPasswordInput = document.getElementById("input_confirm_password");
        confirmPasswordInput.classList.remove("is-invalid");

        if (confirmPasswordInput.value !== this.password) {
            confirmPasswordInput.classList.add("is-invalid");
        } else {
            this.confirmPassword = confirmPasswordInput.value;
        }
    } */

    validateEmail() {
        const emailError = document.getElementById("email_error");
        emailError.innerText = "";
        emailError.classList.add("d-none");

        const email = document.getElementById("input_email").value;
        const regEmail = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        if (!email.toLowerCase().match(regEmail) && email !== "") {
            emailError.innerText = "Invalid email format.";
            emailError.classList.remove("d-none");
            return false;
        } else {
            this.email = email;
            return true;
        }
    }

}

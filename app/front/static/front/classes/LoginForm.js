import managerState from "./ManagerState.js";

export default class LoginForm {
    form = null;
    username = "";
    password = "";

    constructor (form) {
        this.form = form;
        this.form.addEventListener("submit", async (e) => {
            e.preventDefault();
            e.stopPropagation();
            if (this.validate()) {
                const toSend = {
                    username: this.username,
                    password: this.password
                };
				managerState.login( toSend );
                //document.cookie = "csrftoken=; expires=Thu, 01 Jan 1970 00:00:00 UTC";
                return ;
            }
        });
    }

    /* Getters - Setters */

    get getForm() {
        return (this.form);
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
     * @param {string} value
    */
    set setUsername(value) {
        this.username = value;
    }

    /**
     * @param {string} value
    */
    set setPassword(value) {
        this.password = value;
    }

    /* Methods */

    validate() {
        const username = document.getElementById("input_username").value;
        const password = document.getElementById("input_password").value;
        if (username !== "" && password !== "") {
            this.username = username;
            this.password = password;
            this.resetInputs();
            return (true);
        }
        return (false);
    }

    resetInputs() {
        this.form.reset();
        //document.getElementById("input_username").value = "";
        //document.getElementById("input_password").value = "";
    }

}
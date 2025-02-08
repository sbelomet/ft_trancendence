import managerState from "./ManagerState.js";
import managerToast from "./ManagerToast.js";

import { colorToast, endpoints, history_state } from "../utils/utils.js";

class ManagerStatus {
    #response;

    constructor () {}

    /**
     * @returns {Response}
    */
    get #getResponse() {
        return (this.#response);
    }
    
    /**
     * @param {Response} value 
    */
    set #setResponse(value) {
        this.#response = value
    }

    /**
     * @param {Response} response 
     * @returns {Object}
    */
    handleResponse(response) {
        try {
            if ( !(response instanceof Response) ) {
                this.#setResponse = undefined;
                throw new Error("the value is not an instance of Response");
            }
            this.#setResponse = response;
            if (!response.ok) {
                return (this.#returnResponse());
            }
            return (this.#returnResponse(true));
        } catch (error) {
            this.#displayError(500, "Server error");
        }
    }

    /**
     * @param {number} status 
     * @param {string} message 
     * @param {boolean} load 
     */
    handleErrorResponse(status, data, load = false) {
        const message = this.getMessage(data);
        if (status === 413)
            message = "Content Too Large";
        if (load) {
            this.#displayError(status, message);
        } else {
            managerToast.makeToast({
                message: `${status} : ${message}`,
                clickable: false,
                toast_color: colorToast.red
            });
        }
    }

    getMessage(data){
        if (data && typeof data === 'object') {
            // Extract the first available error message
            for (const key in data) {
                if (Array.isArray(data[key])) {
                    return data[key][0]; // Assume it's an array and take the first message
                } else if (typeof data[key] === 'string') {
                    return data[key]; // Directly return if it's a string
                }
            }
        }
        return "Unknown";
    }

    /**
     * @param {number} status
     * @returns {Object}
    */
    async #returnResponse(isOk = false) {
        const status = this.#getResponse.status;
        const data = (status === 205) ? undefined : await this.#resolvePayload();
        return ({
            ok: isOk,
            status: status,
            data: data,
        });
    };

    /* Methods */

    async #resolvePayload() {
        const response = this.#getResponse;
        const contentType = response.headers.get("Content-Type");
        if (contentType && contentType.includes("application/json")) {
            const json = await response.json();
            return (json);
        } else {
            const text = await response.text();
            try {
                const json = await JSON.parse(text);
                return (json);
            } catch (error) {
                return (text);
            }
        }
    };

    #displayError(statusCode, message) {

        const container = document.createElement("div");
        container.setAttribute("class", "container fill_div");
        const div = document.createElement("div");
        div.setAttribute("class", "h-100 d-flex justify-content-center align-items-center");
        const div2 = document.createElement("div");
        div2.setAttribute("class", "text-center");

        const h1 = document.createElement("h1");
        h1.textContent = `Error: ${statusCode}`;
        const h2 = document.createElement("h2");
        h2.textContent = message;

        div2.appendChild(h1);
        div2.appendChild(h2);
        div.appendChild(div2);
        container.appendChild(div);

        let toastContainer;
        const content = document.getElementById("content");
        while (content.lastElementChild) {
            if (content.lastElementChild.id === "no_remove")
                toastContainer = content.lastElementChild;
            content.removeChild(content.lastElementChild);
        };

        if (toastContainer) {
            content.appendChild(toastContainer);
        } else {
            managerToast.init();
        }       

        document.title = `Error: ${statusCode}`;
        window.history.replaceState("", "", "/error/");

        content.appendChild(container);
    }
}

const managerStatus = new ManagerStatus();
Object.freeze(managerStatus);

export default managerStatus;
class ManagerToast {
    #stackToasts = [];
    #parentNode = undefined;

    constructor() {};

    /**
     * @returns {Array}
    */
    get #getStackToast() {
        return (this.#stackToasts);
    };

    /**
     * @returns {HTMLDivElement}
    */
    get #getParentnode() {
        return (this.#parentNode);
    };

    /**
     * @param {Object} value
     */
    set #pushToast( value ) {
        this.#stackToasts.push( value );
    };

    /**
     * @param {HTMLDivElement} value
     */
    set #setParentNode( value ) {
        this.#parentNode = value;
    };

    init() {
        const wrapper = document.createElement("div");
        wrapper.id = "no_remove";
        wrapper.setAttribute("aria-live", "polite");
        wrapper.setAttribute("aria-atomic", "true");
        wrapper.setAttribute("class", "position-relative");

        const toastContainer = document.createElement("div");
        toastContainer.setAttribute("class", "toast-container bottom-0 end-0 p-3");

        wrapper.appendChild( toastContainer );
        const content = document.getElementById("content");
        if (content)
            content.appendChild( wrapper );
        else 
            document.body.appendChild( wrapper );

        this.#setParentNode = toastContainer;
    }

    toastLogs() {
        const toasts = this.#getStackToast;
        //console.log("Toasts logs: ")
        toasts.forEach(( item, index ) => {
            //console.log(`index: ${index + 1}, options: ${item}`);
        });
    }

    #createToast( options ) {
        const toastContainer = document.createElement("div");
        toastContainer.role = "alert";
        toastContainer.ariaAtomic = "true";
        toastContainer.ariaLive = "assertive";
        toastContainer.setAttribute("class", `toast align-items-center border-0 mb-1 ${options.toast_color}`);

        const wrapperDiv = document.createElement("div");
	    wrapperDiv.setAttribute("class", "d-flex");
        
        const toastBody = document.createElement("div");
        toastBody.style = "text-align: justify;";
        toastBody.setAttribute("class", "toast-body text-break m-0");
        toastBody.textContent = (options.clickable && !options.message) ?
            "You have a notification, click me!" : options.message;

        wrapperDiv.appendChild(toastBody);

        if (!options.clickable) {
            const closeButton = document.createElement("button");
            closeButton.type = "button";
            closeButton.ariaLabel = "Close";
            closeButton.setAttribute("data-bs-dismiss", "toast");
            closeButton.setAttribute("class", "btn-close me-2 m-auto");
            wrapperDiv.appendChild(closeButton);
        }

        toastContainer.appendChild( wrapperDiv );

        return (toastContainer);
    }

    /**
     * {
     *   message: undefined/string,
     *   clickable: true/false,
     *   toast_color: colorToast object in utils.js
     * }
    */
    makeToast ( options ) {
        // For debbug, push into array all toast printed
        this.#pushToast = options; // fix

        const toast = this.#createToast( options );

        this.#getParentnode.appendChild( toast );

        const handler = new bootstrap.Toast( toast );
        handler.show();

        if (options.clickable) {
            toast.style = "cursor: pointer;";
            toast.addEventListener('click', (e) => {
                e.preventDefault();
                e.stopPropagation();
                handler.hide();
                const offcanvasChat = document.getElementById('offcanvasChat');
                if (!offcanvasChat.classList.contains('show')) {
                    const openChatButton = document.getElementById('open-chat-btn');
                    openChatButton.click();
                };
                const notificationSection = document.getElementById('notificationSection');
                if (!notificationSection.classList.contains('show')) {
                    const notificationButton = document.getElementById('notification-button');
                    notificationButton.click();
                };
            });
        }

        toast.addEventListener("hidden.bs.toast", (e) => {
            e.preventDefault();
            this.#getParentnode.removeChild(toast);
        });
    }
}

const managerToast = new ManagerToast();
Object.freeze(managerToast);

export default managerToast;
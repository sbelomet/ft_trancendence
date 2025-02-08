const links_elements = Object.freeze([
    {
        li_class: "nav-item",
        anchor: {
            class: "nav-link active",
            path: "/",
            content: "Home"
        }
    },
    {
        li_class: "nav-item border-end border-light",
        anchor: {
            class: "nav-link",
            path: "/about/",
            content: "About"
        }
    },
    {
        li_class: "nav-item",
        anchor: {
            class: "nav-link",
            path: "/hub/",
            content: "Hub"
        }
    },
    {
        li_class: "nav-item ps-2",
        anchor: {
            class: "nav-link",
            path: "/pre_login/",
            content: "Login"
        }
    },
    {
        li_class: "nav-item",
        anchor: {
            class: "nav-link",
            path: "/register/",
            content: "Register"
        }
    }
]);

const user_dropdown = (id) => { return (Object.freeze([
    {
        class: "dropdown-item",
        path: `/profile/${id}/`,
        content: "Profile"
    },
    {
        class: "dropdown-item",
        path: "/settings/",
        content: "Settings"
    }
]))};

export { links_elements, user_dropdown }
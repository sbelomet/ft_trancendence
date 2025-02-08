import managerStatus from "./classes/ManagerStatus.js";
import {
    host,
    methods,
    endpoints
} from "./utils/utils.js";

const getCookie = (name) => {
	if (document.cookie && document.cookie !== '') {
		const cookies = document.cookie.split(';');
		for (let i = 0; i < cookies.length; i++) {
			const cookie = cookies[i].trim();
			if (cookie.substring(0, name.length + 1) === (name + '=')) {
				return (decodeURIComponent(cookie.substring(name.length + 1)));
			}
		}
	}
	return (null);
}

const jsonHeaders = (length, method, is_fragment) => {
	const	headers = new Headers();
	headers.append("Connection", "keep-alive");
	headers.append("Content-Type", "application/json");
	if (length > 0) {}
		headers.append("Content-Length", length);
	if (is_fragment)
		headers.append("fragment", "true");
	headers.append("Accept", "application/json");
	if (method === methods.post) {
		const csrfCookie = getCookie('csrftoken');
		if (csrfCookie)
			headers.append("X-CSRFToken", csrfCookie);
	}
	return (headers);
};

const multipartHeaders = (method) => {
	const	headers = new Headers();
	headers.append("Connection", "keep-alive");
	headers.append("Accept", "*/*");
	if (method === methods.post) {
		const csrfCookie = getCookie('csrftoken');
		if (csrfCookie)
			headers.append("X-CSRFToken", csrfCookie);
	}
	return (headers);
};

const GET_SELF = async (url) => {
	try {
		const response = await fetch(host + url, {
			method: methods.get,
			headers: jsonHeaders(0, methods.get, false),
			credentials: "include"
		});
		return (managerStatus.handleResponse(response));
	} catch (error) {}
};

const GET = async (url, is_fragment = false) => {
	try {
		const response = await fetch(host + url, {
			method: methods.get,
			headers: jsonHeaders(0, methods.get, is_fragment),
			credentials: "include"
		});
		return (managerStatus.handleResponse(response))
	} catch (error) {
		console.error("Error: [api.js]/[GET]");
		console.error(error);
		// message page and redirect
	}
};

const POST_JSON = async (params, resource) => {
	try {
		let body = "";
		if (params)
			body = JSON.stringify(params);
		const	response = await fetch(host + resource, {
			method: methods.post,
			headers: jsonHeaders(body !== "" ? body.length : 0, methods.post, false),
			body: body,
			credentials: "include"
		});
		return (managerStatus.handleResponse(response))
	} catch (error) {
		console.error("Error: [api.js]/[POST_JSON]");
		console.error(error);
		// message page and redirect
	}
};

const POST_MULTIPART = async (params, resource) => {	
	try {
		let bodyContent = new FormData();
		for (const key in params) {
			if (Object.prototype.hasOwnProperty.call(params, key)) {
				bodyContent.append(key, params[key]);
			}
		}
		const	response = await fetch(host + resource, {
			method: methods.post,
			body: bodyContent,
			headers: multipartHeaders(methods.post),
			credentials: "include"
		});
		return (managerStatus.handleResponse(response))
	} catch (error) {
		console.error("Error: [api.js]/[POST_MULTIPART]");
		console.error(error);
		// message page and redirect
	}
};

const PATCH_MULTIPART = async (params, resource) => {
    try {
        let bodyContent = new FormData();
        for (const key in params) {
            if (Object.prototype.hasOwnProperty.call(params, key)) {
                bodyContent.append(key, params[key]);
            }
        }
        const response = await fetch(host + resource, {
            method: methods.patch,
            body: bodyContent,
            headers: {},
            credentials: "include",
        });
        return (managerStatus.handleResponse(response))
    } catch (error) {
        console.error("Error: [api.js]/[PATCH_MULTIPART]");
        console.error(error);
        // message page and redirect
    }
};

const PUT_JSON = async (resource) => {
    try {
        const response = await fetch(host + resource, {
            method: methods.put,
            headers: jsonHeaders(0, methods.put, false),
            credentials: "include",
        });
        return (managerStatus.handleResponse(response))
    } catch (error) {
        console.error("Error: [api.js]/[PUT_JSON]");
        console.error(error);
    }
};

const DELETE = async (url) => { // TO REFACTOR
	try {
		const response = await fetch(makeRequest(host + endpoints.users + "/" + url, methods.delete, params));
		if (!response.ok)
			throw new Error(`Response status: ${response.status}`);
		return (managerStatus.handleResponse(response))
	} catch (error) {
		console.error("Error: [api.js]/[DELETE]");
		console.error(error);
	}
};

export { GET, DELETE, GET_SELF, POST_JSON, PATCH_MULTIPART, POST_MULTIPART, PUT_JSON };
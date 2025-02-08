export class BaseDOMManager {
    constructor() {
   
    }

    createListItem(className = 'list-group-item') {
        const li = document.createElement('li');
        li.className = className;
        return li;
    }

    createButton(text, className, disabled = false) {
        const button = document.createElement('button');
        button.textContent = text;
        button.className = className;
        button.disabled = disabled;
        return button;
    }

    createSpan(text, className = '') {
        const span = document.createElement('span');
        span.textContent = text;
        if (className) span.className = className;
        return span;
    }

    createDiv(className = '') {
        const div = document.createElement('div');
        if (className) div.className = className;
        return div;
    }

    appendChildren(parent, children) {
        children.forEach(child => parent.appendChild(child));
    }

    clearList(listElement) {
        if (listElement) listElement.innerHTML = '';
    }

    createEmptyMessage(container, type) {
        const item = this.createListItem('list-group-item text-center');
        item.textContent = `No ${type.toLowerCase()}s found.`;
        container.appendChild(item);
    }

    createErrorMessage(container, type) {
        const item = this.createListItem('list-group-item text-danger');
        item.textContent = `Error fetching ${type.toLowerCase()}. Please try again later.`;
        container.appendChild(item);
    }
}

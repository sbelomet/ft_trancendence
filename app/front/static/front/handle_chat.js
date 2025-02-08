import { GET, POST_JSON, PUT_JSON } from "./api.js";
import managerState from "./classes/ManagerState.js";
import { endpoints, colorToast } from "./utils/utils.js";
import managerGame from "./classes/game_classes/ManagerGame.js";
import managerToast from "./classes/ManagerToast.js";
import managerStatus from "./classes/ManagerStatus.js";

let myusername;
let myavatar;
let myid;

let lastUsername = null;
let lastUsernamePriv = null;
let lastTime = null;
let lastTimePriv = null;
const newMessageTime = 10000;
const genChatRoomName = 'chat';
let friendsArray = {}; // Stores {'friend.id': 'friend.username'}
let isInert = false;

let chatSocket;

// scrolls to the bottom when messages overflow
function scrollToBottom(activeTabId) {
	if (activeTabId === 'direct-messages-tab') {
		let objDiv = document.getElementById("scroll-thing-dm");
		objDiv.scrollTop = objDiv.scrollHeight;
	} else {
		let objDiv = document.getElementById("scroll-thing");
		objDiv.scrollTop = objDiv.scrollHeight;
	}
}

function getRandomColor() {
	const colors = [
		'#be0aff', '#ff0000', '#ff8700', '#0aefff', '#147df5',
		'#580aff', '#ff4500', '#22d822', '#dc0073', '#00ff00'
	];
	return colors[Math.floor(Math.random() * colors.length)];
}

function setChatLinksInert(toInert = false) {
	const chatCanvas = document.getElementById('offcanvasChat');
    const usernameElements = chatCanvas.querySelectorAll('.chat-username');
	const notificationLinks = chatCanvas.querySelectorAll('.notif-link-button');
	const notifSection = document.getElementById('notificationSection');
	const notifButton = document.getElementById('notification-button');

	usernameElements.forEach(element => {
        if (toInert) {
            element.setAttribute('inert', '');
        } else {
            element.removeAttribute('inert');
		}
    });

	notificationLinks.forEach(element => {
        if (toInert) {
            element.setAttribute('inert', '');
        } else {
            element.removeAttribute('inert');
		}
    });

	if (toInert) {
		if (notifSection.classList.contains('show')) notifButton.click();
		notifButton.setAttribute('inert', '');
	} else {
		notifButton.removeAttribute('inert');
	}

	isInert = toInert;
}

let chatUsers = {};
/**
 * Adds a new message to the HTML
 * It checks the previous message, its user and the time it was posted,
 * to format correctly
 */
function addMessage(data, contentMessage, dbTime = null, timeDiff = null) {
	const currTime = new Date();
	const chatMessages = document.getElementById('chat-messages');

	// Assign a random color to each new user
	if (!chatUsers[data.username]) {
		chatUsers[data.username] = getRandomColor();
	}
	const userColor = chatUsers[data.username];

	/*	If the previous message wasn't sent by the same user, or was sent long enough ago,
		the message is considered a "first message", and will have the username and avatar
		of the sender attached to it.
	*/
	if (lastUsername !== data.username
		|| currTime - lastTime > newMessageTime 
		|| (timeDiff && timeDiff > newMessageTime / 1000)) {

		const messageContainer = document.createElement('div');
		messageContainer.setAttribute("id", "first-message");
		messageContainer.className = 'd-flex align-items-start mt-1';

		const profilePic = document.createElement('img');
		profilePic.src = data.avatarUrl;
		profilePic.alt = 'Profile Picture';
		profilePic.className = 'rounded-circle me-3 ms-1 mt-1';
		profilePic.style.width = '40px';
		profilePic.style.height = '40px';

		const messageContent = document.createElement('div');
		messageContent.className = 'flex-grow-1';
		messageContent.setAttribute('style', 'overflow: auto;');

		const username = document.createElement('a');
		username.className = 'link-primary fw-bold chat-username';
		username.setAttribute('style', `text-decoration: none; -webkit-text-fill-color: ${userColor};`);
		if (isInert) username.setAttribute('inert', '');
		username.role = "button";
		username.innerText = data.username;
		username.addEventListener('click', () => {
			managerState.loadFragmentPage(`/profile/${data.userID}/`);
		});

		const timestamp = document.createElement('small');
		timestamp.className = 'text-muted pe-1';
		if (dbTime) {
			timestamp.innerText = dbTime.substr(dbTime.indexOf("T") + 1, 5);
		} else {
			let hours = currTime.getHours();
			if (hours < 10) {
				hours = "0" + hours;
			}
			let minutes = currTime.getMinutes();
			if (minutes < 10) {
				minutes = "0" + minutes;
			}
			timestamp.innerText = hours + ":" + minutes;
		}

		const header = document.createElement('div');
		header.className = 'd-flex justify-content-between';
		header.appendChild(username);
		header.appendChild(timestamp);

		const messageText = document.createElement('div');
		messageText.setAttribute('style', 'white-space: pre-wrap; word-wrap: break-word; word-break: break-word;');
		messageText.innerText = contentMessage;

		messageContent.appendChild(header);
		messageContent.appendChild(messageText);
		messageContainer.appendChild(profilePic);
		messageContainer.appendChild(messageContent);
		chatMessages.appendChild(messageContainer);
	} else {
		const messageContent = document.createElement('div');
		messageContent.className = 'd-flex';
		messageContent.setAttribute("id", "message-content");
		messageContent.setAttribute('style', 'overflow: auto;');

		const timestamp = document.createElement('small');
		timestamp.setAttribute('id', 'timestamp');
		timestamp.className = 'text-muted me-3 pt-1 ps-1';
		if (dbTime) {
			timestamp.innerText = dbTime.substr(dbTime.indexOf("T") + 1, 5);
		} else {
			let hours = currTime.getHours();
			if (hours < 10) {
				hours = "0" + hours;
			}
			let minutes = currTime.getMinutes();
			if (minutes < 10) {
				minutes = "0" + minutes;
			}
			timestamp.innerText = hours + ":" + minutes;
		}

		const messageText = document.createElement('div');
		messageText.setAttribute('style', 'white-space: pre-wrap; word-wrap: break-word; word-break: break-word;');
		messageText.innerText = contentMessage;

		messageContent.appendChild(timestamp);
		messageContent.appendChild(messageText);
		chatMessages.appendChild(messageContent);
	}

	lastUsername = data.username;
	lastTime = currTime;
}

/**
 * Adds a new message to the HTML
 * It checks the previous message, its user and the time it was posted,
 * to format correctly
 */
function addPrivMessage(data, contentMessage, dbTime = null, timeDiff = null) {
	const currTime = new Date();
	const chatMessages = document.getElementById('dm-messages');

	// Assign a random color to each new user
	if (!chatUsers[data.username]) {
		chatUsers[data.username] = getRandomColor();
	}
	const userColor = chatUsers[data.username];

	/*	If the previous message wasn't sent by the same user, or was sent long enough ago,
		the message is considered a "first message", and will have the username and avatar
		of the sender attached to it.
	*/
	if (lastUsernamePriv !== data.sender_username
		|| currTime - lastTimePriv > newMessageTime 
		|| (timeDiff && timeDiff > newMessageTime / 1000)) {

		const messageContainer = document.createElement('div');
		messageContainer.setAttribute("id", "first-message");
		messageContainer.className = 'd-flex align-items-start mt-1';

		const profilePic = document.createElement('img');
		profilePic.src = data.avatarUrl;
		profilePic.alt = 'Profile Picture';
		profilePic.className = 'rounded-circle me-3 ms-1 mt-1';
		profilePic.style.width = '40px';
		profilePic.style.height = '40px';

		const messageContent = document.createElement('div');
		messageContent.className = 'flex-grow-1';
		messageContent.setAttribute('style', 'overflow: auto;');

		const username = document.createElement('a');
		username.className = 'link-primary fw-bold chat-username';
		username.setAttribute('style', `text-decoration: none; -webkit-text-fill-color: ${userColor};`);
		if (isInert) username.setAttribute('inert', '');
		username.role = "button";
		username.innerText = data.sender_username;
		username.addEventListener('click', () => {
			managerState.loadFragmentPage(`/profile/${data.senderID}/`);
		});

		const timestamp = document.createElement('small');
		timestamp.className = 'text-muted pe-1';
		if (dbTime) {
			timestamp.innerText = dbTime.substr(dbTime.indexOf("T") + 1, 5);
		} else {
			let hours = currTime.getHours();
			if (hours < 10) {
				hours = "0" + hours;
			}
			let minutes = currTime.getMinutes();
			if (minutes < 10) {
				minutes = "0" + minutes;
			}
			timestamp.innerText = hours + ":" + minutes;
		}

		const header = document.createElement('div');
		header.className = 'd-flex justify-content-between';
		header.appendChild(username);
		header.appendChild(timestamp);

		const messageText = document.createElement('div');
		messageText.setAttribute('style', 'white-space: pre-wrap; word-wrap: break-word; word-break: break-word;');
		messageText.innerText = contentMessage;

		messageContent.appendChild(header);
		messageContent.appendChild(messageText);
		messageContainer.appendChild(profilePic);
		messageContainer.appendChild(messageContent);
		chatMessages.appendChild(messageContainer);
	} else {
		const messageContent = document.createElement('div');
		messageContent.className = 'd-flex';
		messageContent.setAttribute("id", "message-content");
		messageContent.setAttribute('style', 'overflow: auto;');

		const timestamp = document.createElement('small');
		timestamp.setAttribute('id', 'timestamp');
		timestamp.className = 'text-muted me-3 pt-1 ps-1';
		if (dbTime) {
			timestamp.innerText = dbTime.substr(dbTime.indexOf("T") + 1, 5);
		} else {
			let hours = currTime.getHours();
			if (hours < 10) {
				hours = "0" + hours;
			}
			let minutes = currTime.getMinutes();
			if (minutes < 10) {
				minutes = "0" + minutes;
			}
			timestamp.innerText = hours + ":" + minutes;
		}

		const messageText = document.createElement('div');
		messageText.setAttribute('style', 'white-space: pre-wrap; word-wrap: break-word; word-break: break-word;');
		messageText.innerText = contentMessage;

		messageContent.appendChild(timestamp);
		messageContent.appendChild(messageText);
		chatMessages.appendChild(messageContent);
	}

	lastUsernamePriv = data.sender_username;
	lastTimePriv = currTime;
}

// Function to add notification to the UI
function addNotification(data) {
	// Assign a random color to each new user
	if (!chatUsers[data.username]) {
		chatUsers[data.username] = getRandomColor();
	}
	const userColor = chatUsers[data.username];

	const notificationSection = document.getElementById('notificationSection');
	const notificationBody = notificationSection.querySelector('.list-group');
	const noNotificationElement = notificationBody.querySelector('p');
	if (noNotificationElement && noNotificationElement.textContent === "No new notifications") {
		notificationBody.removeChild(noNotificationElement);
	}
	
	const notificationElement = document.createElement('li');
	notificationElement.className = 'list-group-item ';
	const textPart = document.createElement('div');
	const actionPart = document.createElement('div');
	if (data.notification === 'friendReq') {
		const sender = document.createElement('a');
		sender.className = 'link-primary fw-bold chat-username';
		sender.role = 'button';
		sender.setAttribute('style', `text-decoration: none; -webkit-text-fill-color: ${userColor};`);
		if (isInert) sender.setAttribute('inert', '');
		sender.textContent = `${data.senderName}`;
		sender.addEventListener('click', () => {
			managerState.loadFragmentPage(`/profile/${data.senderID}/`);
		});
		textPart.appendChild(sender);
		const baseText = document.createElement('span');
		baseText.innerText = ' wants to be friends';
		textPart.appendChild(baseText);
		
		const acceptButton = document.createElement('button');
		const ignoreButton = document.createElement('button');
		acceptButton.className = "btn btn-bd-primary me-1 my-1 p-1 notif-link-button";
		ignoreButton.className = "btn btn-bd-primary p-1 notif-link-button";
		acceptButton.setAttribute('style', 'font-size: .8rem;');
		ignoreButton.setAttribute('style', 'font-size: .8rem;');
		if (isInert) acceptButton.setAttribute('inert', '');
		if (isInert) ignoreButton.setAttribute('inert', '');
		acceptButton.textContent = 'Accept';
		ignoreButton.textContent = 'Ignore';
		acceptButton.addEventListener('click', async function() {
			notificationElement.remove();
			const response = await PUT_JSON(endpoints.acceptFriendship(data.requestID));
			if (!response.ok) managerStatus.handleErrorResponse(response.status, {message: "Couldn't access friendship"}, false);
			ifNoNotifs(notificationBody);
			await fetchFriends();
			removeNotification(data);
		});
		ignoreButton.addEventListener('click', async function() {
			notificationElement.remove();
			const response = await PUT_JSON(endpoints.refuseFriendship(data.requestID));
			if (!response.ok) managerStatus.handleErrorResponse(response.status, {message: "Couldn't access friendship"}, false);
			ifNoNotifs(notificationBody);
			removeNotification(data);
		});
		actionPart.appendChild(acceptButton);
		actionPart.appendChild(ignoreButton);
	} 
	else if (data.notification === 'gameInvite') {
		const sender = document.createElement('a');
		sender.className = 'link-primary fw-bold chat-username';
		sender.role = 'button';
		sender.setAttribute('style', `text-decoration: none; -webkit-text-fill-color: ${userColor};`);
		if (isInert) sender.setAttribute('inert', '');
		sender.textContent = `${data.senderName}`;
		sender.addEventListener('click', () => {
			managerState.loadFragmentPage(`/profile/${data.senderID}/`);
		});
		textPart.appendChild(sender);
		const baseText = document.createElement('span');
		baseText.innerText = ' wants to play';
		textPart.appendChild(baseText);

		const acceptButton = document.createElement('button');
		const ignoreButton = document.createElement('button');
		acceptButton.className = "btn btn-bd-primary me-1 my-1 p-1 notif-link-button";
		ignoreButton.className = "btn btn-bd-primary p-1 notif-link-button";
		acceptButton.setAttribute('style', 'font-size: .8rem;');
		ignoreButton.setAttribute('style', 'font-size: .8rem;');
		if (isInert) acceptButton.setAttribute('inert', '');
		if (isInert) ignoreButton.setAttribute('inert', '');
		acceptButton.textContent = 'Join';
		ignoreButton.textContent = 'Ignore';
		acceptButton.addEventListener('click', function() {
			notificationElement.remove();
			managerGame.initGame(endpoints.joinGame(data.requestID, 'remote'), 'remote');
			ifNoNotifs(notificationBody);
			removeNotification(data);
		});
		ignoreButton.addEventListener('click', function() {
			notificationElement.remove();
			ifNoNotifs(notificationBody);
			removeNotification(data);
		});
		actionPart.appendChild(acceptButton);
		actionPart.appendChild(ignoreButton);
	}
	else if (data.notification === 'tourneyInvite') {
		const sender = document.createElement('a');
		sender.className = 'link-primary fw-bold chat-username';
		sender.role = 'button';
		sender.setAttribute('style', `text-decoration: none; -webkit-text-fill-color: ${userColor};`);
		if (isInert) sender.setAttribute('inert', '');
		sender.textContent = `${data.senderName}`;
		sender.addEventListener('click', () => {
			managerState.loadFragmentPage(`/profile/${data.senderID}/`);
		});
		textPart.appendChild(sender);
		const baseText = document.createElement('span');
		baseText.innerText = ' wants to play a tournament';
		textPart.appendChild(baseText);

		const acceptButton = document.createElement('button');
		const ignoreButton = document.createElement('button');
		acceptButton.className = "btn btn-bd-primary me-1 my-1 p-1 notif-link-button";
		ignoreButton.className = "btn btn-bd-primary p-1 notif-link-button";
		acceptButton.setAttribute('style', 'font-size: .8rem;');
		ignoreButton.setAttribute('style', 'font-size: .8rem;');
		if (isInert) acceptButton.setAttribute('inert', '');
		if (isInert) ignoreButton.setAttribute('inert', '');
		acceptButton.textContent = 'Join';
		ignoreButton.textContent = 'Ignore';
		acceptButton.addEventListener('click', async function() {
			notificationElement.remove();
			const response = await POST_JSON({}, endpoints.joinTournament(data.requestID));
			if (!response.ok) managerStatus.handleErrorResponse(response.status, {message: "Couldn't join tournament"}, false);
			ifNoNotifs(notificationBody);
			removeNotification(data);
		});
		ignoreButton.addEventListener('click', async function() {
			notificationElement.remove();
			ifNoNotifs(notificationBody);
			removeNotification(data);
		});
		actionPart.appendChild(acceptButton);
		actionPart.appendChild(ignoreButton);
	}
	else if (data.notification === 'systemMessage') {
		const baseText = document.createElement('span');
		baseText.innerText = data.message;
		textPart.appendChild(baseText);

		const acceptButton = document.createElement('button');
		acceptButton.className = "btn btn-bd-primary me-1 my-1 p-1 notif-link-button";
		acceptButton.setAttribute('style', 'font-size: .8rem;');
		if (isInert) acceptButton.setAttribute('inert', '');
		acceptButton.textContent = 'YAAAAY!!';
		acceptButton.addEventListener('click', async function() {
			notificationElement.remove();
			ifNoNotifs(notificationBody);
		});
		actionPart.appendChild(acceptButton);
	}
	
	notificationElement.appendChild(textPart);
	notificationElement.appendChild(actionPart);
	notificationBody.appendChild(notificationElement);
	
	// Show the notification badge on the notifications button
	const notificationBadge = document.getElementById('notification-badge');
	if (!notificationSection.classList.contains('show')) {
		notificationBadge.style.display = 'inline';
	}

	// Show the notification badge on the open chat button
	const openchatNotificationBadge = document.getElementById('openchat-notification-badge');
	if (!document.getElementById('offcanvasChat').classList.contains('show')) {
		openchatNotificationBadge.style.display = 'inline';
	}
}

function showToast(notification) {
	const data = {
		message: notification.message || "WOW A NOTIFICATION???",
		clickable: notification.message || isInert ? false : true,
		toast_color: colorToast.blue
	};

	managerToast.makeToast(data);
}

function showCountdownOverlay(data) {
	if (data.message) {
		const overlay = document.getElementById('countdown-overlay');
		const countdownTitle = document.getElementById('countdown-text');
		const countdownTimer = document.getElementById('countdown-timer');
		let countdown = 5;

		overlay.className = 'position-fixed top-0 start-0 w-100 h-100 d-flex flex-column justify-content-center align-items-center';
		countdownTitle.textContent = `Your match against ${data.opponent_name} is about to begin!`;
		countdownTimer.textContent = countdown;

		const interval = setInterval(() => {
			countdown -= 1;
			countdownTimer.textContent = countdown;

			if (countdown <= 0) {
				clearInterval(interval);
				overlay.className = 'd-none';
			}
		}, 1000);
	} else {
		managerGame.initGame(endpoints.joinGame(data.game_id, 'remote'), 'remote');
	}
}

function ifNoNotifs(notificationBody) {
	if (notificationBody.children.length === 0) {
		const noNotificationElement = document.createElement('p');
		noNotificationElement.className = 'm-0 text-center';
		noNotificationElement.textContent = "No new notifications";
		notificationBody.appendChild(noNotificationElement);
	}
}

// Function to send a notification
function sendNotification(notification, friendData, requestData) {
	if (requestData) {
		chatSocket.send(JSON.stringify({
			'type': 'notification',
			'notification': notification,
			'message': '',
			'senderID': myid,
			'senderName': myusername,
			'recipientID': friendData.id,
			'requestID': requestData.id
		}));
	}
}

// Function to remove a notification
function removeNotification(data) {
	const notificationID = data.id ? data.id : data.notificationID
	chatSocket.send(JSON.stringify({
		'type': 'remove_notification',
		'notificationID': notificationID
	}));
}

// Send a friend request notification
function sendFriendRequestNotification(friendData, friendRequestData) {
	const notification = 'friendReq';
	sendNotification(notification, friendData, friendRequestData);
}

// Send a game invite notification
function sendInviteNotification(friendData, gameData) {
	const notification = 'gameInvite';
	sendNotification(notification, friendData, gameData);
}

function sendTourneyInviteNotification(friendData, tourneyID) {
	const notification = 'tourneyInvite';
	const tourneyData = { id: tourneyID };
	sendNotification(notification, friendData, tourneyData);
}

async function fetchFriends() {
	await GET(endpoints.userFriends(myid)) // Fetch the connected users friends
		.then(response => {
			const friendsDropdown = document.getElementById('friends-dropdown');
			for (var i = friendsDropdown.options.length - 1; i > 0; i--) {
				friendsDropdown.removeChild(friendsDropdown.options[i]);
			}
			friendsDropdown.selectedIndex = 0;
			response.data.forEach(friend => { // Poplate frends dropdown
				const option = document.createElement('option');
				option.value = friend.id;
				option.textContent = friend.username;
				friendsDropdown.appendChild(option);
				friendsArray[friend.id] = friend.username;
			});
		});
}

/**
 * Fetches the messages stored in the database by using an API, then calls addMessage() for each of them
 */
async function fetchMessages(url = endpoints.generalMessages) {
	await GET(url)
		.then(response => {
			const data = response.data;
			data.results.forEach(message => {
				addMessage(message, message.content, message.date_added, message.time_diff);
			});
			scrollToBottom('general-chat-tab');
			if (data.next) {
				fetchMessages(data.next);
			}
		});
}

/**
 * Fetches the private messages stored in the database by using an API, then calls addMessage() for each of them
 */
async function fetchPrivateMessages(url = endpoints.privateMessages, otherUser = null) {
	let fullURL;
	if (otherUser) {
		fullURL = url + '?other_user=' + otherUser;
	} else {
		fullURL = url;
	}

	await GET(fullURL)
		.then(response => {
			const data = response.data;
			data.results.forEach(message => {
				addPrivMessage(message, message.content, message.date_added, message.time_diff);
			});
			scrollToBottom('direct-messages-tab');
			if (data.next) {
				fetchPrivateMessages(data.next);
			}
		});
}

async function fetchNotifications(url = endpoints.notifications) {
	await GET(url)
		.then(response => {
			const data = response.data;
			data.results.forEach(notif =>{
				addNotification(notif);
			});
			if (data.next) {
				fetchNotifications(data.next);
			}
		});
}

//--- Chat Socket Setup ---//
function setupChatSocket() {
	chatSocket = new WebSocket(
		'wss://'
		+ window.location.host
		+ '/ws/chat/'
		+ genChatRoomName
		+ '/'
	);
	
	chatSocket.onmessage = function(e) {
		const data = JSON.parse(e.data);
		if (data.type === 'chat_message') {
			if (data.message) {
				addMessage(data, data.message);
				scrollToBottom('general-chat-tab');
			}
		} else if (data.type === 'private_chat_message') {
			const friendsDropdown = document.getElementById('friends-dropdown');
			const selectedFriend = friendsDropdown.options[friendsDropdown.selectedIndex].value;
			if (data.message && (data.senderID == selectedFriend || data.senderID === myid)) {
				addPrivMessage(data, data.message);
				scrollToBottom('direct-messages-tab');
			}
		} else if (data.type === 'notification') {
			if (data.message === '') addNotification(data);
			showToast(data);
		} else if (data.type === 'tournament_update') {
			showCountdownOverlay(data); // countdown and start game
		} else if (data.type === 'tournament_ping') {
			chatSocket.send(JSON.stringify({
				'type': 'ping_response',
				'user_id': myid,
				'tournament_id': data.ping_id
			}));
		}
	};

	chatSocket.onclose = function(e) {
	};
}

function closeChatSocket() {
	if (chatSocket && chatSocket.readyState === WebSocket.OPEN) {
		chatSocket.close();
	}
}

// Override input and submit for gen chat
function genChatSubmit(username, avatarUrl, userID) {
	const messageInputDom = document.getElementById('chat-message-input');
	const messageSubmitDom = document.getElementById('chat-message-submit');
	const messageErrorDom = document.getElementById('message-error');

	messageInputDom.placeholder = 'Message general chat';
	messageInputDom.focus();
	messageInputDom.onkeyup = function(e) {
		if (e.key === 'Enter') {  // enter, return
			messageSubmitDom.click();
		}
	};

	messageSubmitDom.onclick = function(e) {
		const message = messageInputDom.value;
		if (message.length > 200) {
            messageErrorDom.style.display = 'block';
			setTimeout(() => {
                messageErrorDom.style.display = 'none';
            }, 3500); // Hide the error message after 5 seconds
			messageInputDom.value = '';
			messageInputDom.focus();
            return;
        } else {
            messageErrorDom.style.display = 'none';
        }
		if (message.trim()) {
			chatSocket.send(JSON.stringify({
				'type': 'chat_message',
				'message': message,
				'username': username,
				'avatarUrl': avatarUrl,
				'userID': userID,
				'room': genChatRoomName
			}));
		}
		messageInputDom.value = '';
		messageInputDom.focus();
	};
}

// Override input and submit for dms
function privChatSubmit(friendID, myusername, avatarUrl, userID) {
	const messageInputDom = document.getElementById('chat-message-input');
	const messageSubmitDom = document.getElementById('chat-message-submit');
	const messageErrorDom = document.getElementById('message-error');

	messageInputDom.placeholder = friendsArray[friendID] ? `Message ${friendsArray[friendID]}` : 'Message friend';
	messageInputDom.focus();
	messageInputDom.onkeyup = function(e) {
		if (e.key === 'Enter') {  // enter, return
			messageSubmitDom.click();
		}
	};
	
	messageSubmitDom.onclick = function(e) {
		const message = messageInputDom.value;
		if (message.length > 200) {
            messageErrorDom.style.display = 'block';
			setTimeout(() => {
                messageErrorDom.style.display = 'none';
            }, 3500); // Hide the error message after 5 seconds
			messageInputDom.value = '';
			messageInputDom.focus();
            return;
        } else {
            messageErrorDom.style.display = 'none';
        }
		if (message.trim() && friendID) {
			chatSocket.send(JSON.stringify({
				'type': 'private_chat_message',
				'message': message,
				'sender_username': myusername,
				'avatarUrl': avatarUrl,
				'senderID': userID,
				'recipientID': friendID
			}));
		}
		messageInputDom.value = '';
		messageInputDom.focus();
	};
}


async function chatEntrypoint() {
	document.getElementById('open-chat-btn').addEventListener('click', function(e) {
		e.preventDefault();
		const notificationBadge = document.getElementById('openchat-notification-badge');
		notificationBadge.style.display = 'none';
		document.getElementById('chat-message-input').focus();
	});

	myusername = managerState.getUser.username;
	myavatar = managerState.getUser.avatar;
	myid = managerState.getUserID;

	await fetchFriends();

	await GET(endpoints.userBlocked(myid))
		.then(response => {
			const data = response.data;
			data.forEach(user => {
				if (user.id in friendsArray) {
					delete friendsArray[user.id];
				}
			});
		});

	setupChatSocket(); // Create general chat websocket
	fetchMessages(); // Initial load of messages
	genChatSubmit(myusername, myavatar, myid); // setup submit for gen chat
	fetchNotifications();

	const friendsDropdown = document.getElementById('friends-dropdown');
	friendsDropdown.addEventListener('change', function(e) { // Add an event listener for when a friend is selected
		e.preventDefault();
		lastUsernamePriv = null;
		lastTimePriv = null;
		document.getElementById('dm-messages').innerHTML = '';
		const selectedIndex = friendsDropdown.selectedIndex;
		const selectedFriend = friendsDropdown.options[selectedIndex].value;
		if (selectedFriend in friendsArray) { // If a friend is selected (and not the 'Select a friend option'), setup websocket
			document.querySelector('#chat-message-input').disabled = false;
			document.querySelector('#chat-message-submit').disabled = false;
			fetchPrivateMessages(undefined, selectedFriend);
			privChatSubmit(selectedFriend, myusername, myavatar, myid);
		} else {
			document.querySelector('#chat-message-input').disabled = true;
			document.querySelector('#chat-message-submit').disabled = true;
			privChatSubmit(null, myusername, myavatar, myid);
		}
	});

	const chatTabs = document.getElementById('chatTabs');
	chatTabs.addEventListener('shown.bs.tab', function(e) { // Add an event listener for when tabs are switched
		e.preventDefault();
		const activeTab = e.target; // The newly activated tab
		const activeTabId = activeTab.getAttribute('id');
		document.querySelector('#chat-message-input').disabled = false;
		document.querySelector('#chat-message-submit').disabled = false;
		if (activeTabId === 'direct-messages-tab') {
			const friendsDropdown = document.getElementById('friends-dropdown');
			const selectedIndex = friendsDropdown.selectedIndex;
			const selectedFriend = friendsDropdown.options[selectedIndex].value;
			if (selectedFriend in friendsArray) {
				privChatSubmit(selectedFriend, myusername, myavatar, myid);
			} else {
				document.querySelector('#chat-message-input').disabled = true;
				document.querySelector('#chat-message-submit').disabled = true;
				privChatSubmit(null, myusername, myavatar, myid);
			}
		} else {
			genChatSubmit(myusername, myavatar, myid);
		}
	});

	// Hide the notification badge when the notifications section is expanded
	document.getElementById('notification-button').addEventListener('click', function(e) {
		e.preventDefault();
		const notificationBadge = document.getElementById('notification-badge');
		notificationBadge.style.display = 'none';
	});
}

export {
	chatEntrypoint,
	sendFriendRequestNotification,
	sendInviteNotification,
	sendTourneyInviteNotification,
	closeChatSocket,
	setChatLinksInert
};
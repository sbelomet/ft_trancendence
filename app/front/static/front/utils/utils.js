const methods = Object.freeze({
    get: "GET",
    put: "PUT",
    post: "POST",
    patch: "PATCH",
    delete: "DELETE"
});

const endpoints = Object.freeze({
    home: "/",
    hub: "/hub/",
    game: "/game/",
    about: "/about/",
    login: "/api/login/",
    logout: "/api/logout/",
    register: "/api/register/",
    redirect: "/redirect/",
    createGame: "/api/create-game/",
	otp: "/api/otp_verif/",
	oauth: "/api/oauth_login/",

    users: "/api/users/",
    userDetails: (id) => `/api/users/${id}/`,
	userFriends: (id) => `/api/users/${id}/see_friend_friends/`,
	userBlocked: (id) => `/api/users/${id}/see_blocked_users/`,
    //createGame: "/api/create-game/"
    games: '/api/games/',
    gameDetails: (id) => `/api/games/${id}/`,
    joinGame: (id, type) => `wss://${window.location.host}/ws/server_side_pong/${type}/${id}/`,
    //abortParticipation: (id) => `/api/games/${id}/abort_participation/`,
    invitations: '/api/invitations/',
    invitationDetails: (id) => `/api/invitations/${id}/`,
    acceptInvitation: (id) => `/api/invitations/${id}/accept_invitation/`,
    refuseInvitation: (id) => `/api/invitations/${id}/refuse_invitation/`,

    tournaments: '/api/tournaments/',
    tournamentDetails: (id) => `/api/tournaments/${id}/`,
    joinTournament: (id) => `/api/tournaments/${id}/join/`,
    withdrawTournament: (id) => `/api/tournaments/${id}/withdraw/`,
    startTournament: (id) => `/api/tournaments/${id}/start_tournament/`,

    statistics: '/api/statistics/',
    profileStatistics: (id) => `/api/statistics/${id}/`,

    players: '/api/players/',
    playerDetails: (id) => `/api/players/${id}/`,
    history: (id, type) => `/api/players/${id}/history/${type}/`,

    ranking: '/api/ranking/',
    friendships: '/api/friendships/',
	acceptFriendship: (id) => `/api/friendships/${id}/accept_friendship/`,
	refuseFriendship: (id) => `/api/friendships/${id}/refuse_friendship/`,

	generalMessages: '/api/chat/messages/',
	privateMessages: '/api/chat/private-messages/',
	notifications: '/api/chat/notifications'
});

const fragments = Object.freeze({
    chat_modal: "/chat_modal/"
})

const select_auth = Object.freeze({
    none: "none",
    email: "email",
    application: "totp",
});

const history_state = Object.freeze({
    push: "push",
    nopush: "nopush",
    replace: "replace"
});

const currentProfile = {
    id: -1,
    current: undefined
};

const colorToast = Object.freeze({
    red: "text-bg-danger",
    green: "text-bg-success",
    blue: "text-bg-info"
})

const host = window.location.origin !== null ? window.location.origin : 'https://localhost:2000';

export {
    currentProfile,
    history_state,
    select_auth,
    colorToast,
    fragments,
    endpoints,
    methods,
    host
};
import { POST_JSON } from "../../api.js";
import managerState from "../ManagerState.js";
import managerToast from "../ManagerToast.js";
import { colorToast, endpoints, history_state } from "../../utils/utils.js";

class ManagerGame {
    #error = false;
    #is_ended = false;
    #state = undefined;
    #users = undefined;
    #is_tournament = false;
    #game_type = undefined;
    #final_score = undefined;
    #game_socket = undefined;

    constructor() {}

    get getError() {
        return (this.#error);
    }

    get getUsers() {
        return (this.#users);
    }

    get getIsEnded() {
        return (this.#is_ended);
    }

    get getState() {
        return (this.#state);
    }

    get getGameType() {
        return (this.#game_type);
    }
    
    get #getGameSocket() {
        return (this.#game_socket);
    }

    get getFinalScore() {
        return (this.#final_score);
    }

    get getIsTournament() {
        return (this.#is_tournament);
    }

    get getHaveWebsocket() {
        if (this.#game_socket != undefined)
            return (true);
        return (false);
    }

    /**
     * @param {boolean} value
    */
    set #setError(value) {
        this.#error = value;
    }

    /**
     * @param {Object} value
    */
    set #setUsers(value) {
        this.#users = value;
    }

    /**
     * @param {boolean} value
    */
    set #setIsEnded(value) {
        this.#is_ended = value;
    }

    /**
     * @param {Object} newState
    */
    set #setState(newState) {
        this.#state = newState;
    }

    /**
     * @param {string} value
    */
    set #setgameType(value) {
        this.#game_type = value;
    }

    /**
     * @param {Object} newSocket
    */
    set #setGameSocket(newSocket) {
        this.#game_socket = newSocket;
    }

    /**
     * @param {boolean} value
    */
    set #setIsTournament(value) {
        this.#is_tournament = value;
    }

    /**
     * @param {Object} scores
    */
    set #setFinalScore(scores) {
        this.#final_score = scores;
    }

    async initGame(url, gameType) {
        try {
            this.#setgameType = gameType;
            this.#setGameSocket = new WebSocket(url);
            this.#getGameSocket.onmessage = (e) => {
                if (!this.getIsEnded) {
                    const data = JSON.parse(e.data);
                    switch (data.type) {
                        case "init":
                            this.#setIsTournament = data.tournament ? data.tournament : false ;
                            this.#setUsers = { player1Name: data.player1, player2Name: data.player2 };
                            managerState.loadFragmentPage(endpoints.game, history_state.nopush);
                            break ;
                        case "gameplay":
                            this.#setState = data.state;
                            break ;
                        case "disconnection":
                            this.#setIsEnded = true;
                            this.#handleDisconnection(data);
                            break ;
                        case "ending":
                            this.#setIsEnded = true;
                            this.#setFinalScore = {scores:data.score, winnerId: data.winnerId};
                            break ;
                        default:
                            break ;
                    };
                };
            };
        } catch (err) {
            this.#setError = true;
            this.#setIsEnded = true;
        }
    }

    #handleDisconnection(data) {
        const users = this.getUsers;
        if (data.winner === users.player1Name)
            this.#setFinalScore = {scores: {player1: 1, player2: 0}};
        else
            this.#setFinalScore = {scores: {player1: 0, player2: 1}};
    }

    action(move, role, action) {
        try {
            this.#getGameSocket.send(JSON.stringify({
                role: role,
                movement: move,
                type: "gameplay",
				action: action
            })); 
        } catch (err) {
            this.#setError = true;
            this.#setIsEnded = true;
        }
    }

    closeConnection() {
        if (this.#getGameSocket !== undefined) {
            this.#getGameSocket.close();
            this.#setGameSocket = undefined;
        }
        this.#setIsEnded = false;
        this.#setUsers = undefined;
    }

    async createNewGame(data) {
        try {
            const response = await POST_JSON(data, endpoints.games);
            if (!response.ok) {
                return ({
                    ok: false,
                    message: response.data
                });
            } else {
                const responseData = response.data;
                return ({
                    ok: true,
                    gameId: responseData.game_id,
                    game_type: responseData.game_type,
                    url: endpoints.joinGame(responseData.game_id, responseData.game_type),
                });
            }  
        } catch (error) {
            managerToast.makeToast({
                message: "Error when trying to create an game instance",
                clickable: false,
                toast_color: colorToast.red
            });
        }
    }
}

const managerGame = new ManagerGame();
Object.freeze(managerGame);

export default managerGame;
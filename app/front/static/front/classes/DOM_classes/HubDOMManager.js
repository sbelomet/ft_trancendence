// HubDOMManager.js
import { BaseDOMManager } from "./BaseDOMManager.js";
import { formatDateTime, getUserInfo } from "../../utils/functions_utils.js";

export class HubDOMManager extends BaseDOMManager {
    constructor() {
        super(); //le constructeur de BaseDOMManager
        this.initializeElements();
    }

    initializeElements() {
        this.elements = {
            createGameBtn: document.getElementById("create_game_btn"),
            createTournamentBtn: document.getElementById("create_tournament_btn"),
            playerRankingBtn: document.getElementById("player_ranking_btn"),
            gamesList: document.getElementById("scheduled_games_list"),
            tournamentsList: document.getElementById("scheduled_tournaments_list"),
            statisticsList: document.getElementById("statistics_list"),
            matchHistoryList: document.getElementById("match_history_list"),
            tournamentHistoryList: document.getElementById("tournament_history_list"),
            rankingList: document.getElementById("ranking_list"),
            friendsList: document.getElementById("friends_list")
        };
    }

    createGameListItem(game, currentUserId, actions) {
        const li = this.createListItem('list-group-item position-relative');
        
        const titleDiv = this.createDiv();
        const titleStrong = document.createElement('strong');
        titleStrong.textContent = 'Game: ';
        titleDiv.appendChild(titleStrong);
        titleDiv.appendChild(document.createTextNode(game.name));

        const typeDiv = this.createDiv();
        const typeStrong = document.createElement('strong');
        typeStrong.textContent = 'Type of game: ';
        typeDiv.appendChild(typeStrong);
        typeDiv.appendChild(document.createTextNode(game.game_type || "Unknown Type"));

        this.appendChildren(li, [titleDiv, typeDiv]);

		// Identify roles
		const isCreator = (game.created_by === currentUserId);
		const isPlayer = (game.player1 === currentUserId) || (game.player2 === currentUserId);
		
		// Remote game logic
		if (game.game_type === 'remote') {
			// 1. If the user is the creator, show Invite button
			if (isCreator) {
				const inviteBtn = this.createButton('Invite', 'btn btn-bd-primary btn-sm action-btn');
				inviteBtn.addEventListener('click', async () => actions.onInvite(game));
				li.appendChild(inviteBtn);
			} 
			// 2. If the user is not the creator, not a player => show Join
			else if (!isPlayer) {
				const joinBtn = this.createButton('Join', 'btn btn-bd-primary btn-sm action-btn');
				joinBtn.addEventListener('click', () => actions.onJoin(game.id, game.game_type));
				li.appendChild(joinBtn);
			}
		}
		// Local game logic: show "Start" if user is not a player
		else if (game.game_type === "local" && !isPlayer) {
			const joinBtn = this.createButton('Start', 'btn btn-bd-primary btn-sm action-btn');
			joinBtn.addEventListener('click', () => actions.onJoin(game.id, game.game_type));
			li.appendChild(joinBtn);
		}
        return (li);
    }

    createTournamentListItem(tournament, currentUser, actions) {
        const li = this.createListItem('list-group-item position-relative');
        
        const titleDiv = this.createDiv();
        const titleStrong = document.createElement('strong');
        titleStrong.textContent = 'Tournament: ';
        titleDiv.appendChild(titleStrong);
        titleDiv.appendChild(document.createTextNode(tournament.name));

        const dateDiv = this.createDiv();
        const dateStrong = document.createElement('strong');
        dateStrong.textContent = 'Scheduled Date: ';
        dateDiv.appendChild(dateStrong);
        dateDiv.appendChild(document.createTextNode(
            tournament.start_time ? formatDateTime(tournament.start_time) : "Unknown Date"
        ));

        const descriptionDiv = this.createDiv();
        const descriptionStrong = document.createElement('strong');
        descriptionStrong.textContent = 'Description: ';
        descriptionDiv.appendChild(descriptionStrong);
        descriptionDiv.appendChild(document.createTextNode(tournament.description));

        this.appendChildren(li, [titleDiv, dateDiv, descriptionDiv]);

        const button = this.createTournamentButton(tournament, currentUser, actions);
        if (button) li.appendChild(button);

        return li;
    }

    createTournamentButton(tournament, currentUser, actions) {
        const isParticipant = tournament.participants.some(
            participant => participant.user_id === currentUser.id
        );
        const hasCapacity = tournament.participants.length < tournament.max_players;

        if (!isParticipant && hasCapacity) {
            const btn = this.createButton('Join', 'btn btn-bd-primary btn-sm action-btn');
            btn.addEventListener('click', () => actions.onJoin(tournament.id));
            return btn;
        } else if (isParticipant && hasCapacity) {
            const btn = this.createButton('Options', 'btn btn-bd-primary btn-sm action-btn');
            btn.addEventListener('click', () => actions.onOptions(tournament));
            return btn;
        } else if (isParticipant && !hasCapacity) {
            const btn = this.createButton('Withdraw', 'btn btn-bd-primary btn-sm action-btn');
            btn.addEventListener('click', () => actions.onWithdraw(tournament.id));
            return btn;
        }
        return null;
    }

    updateStatistics(stats) {
        this.clearList(this.elements.statisticsList);
        
        const statsMapping = {
            matches_played: "Matches played",
            matches_won: "Matches won",
            win_rate: "Win rate",
            tournaments_played: "Tournaments played",
            tournaments_won: "Tournaments won",
            tournament_win_rate: "Tournament win rate"
        };

        Object.entries(statsMapping).forEach(([key, label]) => {
            const li = this.createListItem();
            const strong1 = document.createElement('strong');
            strong1.textContent = `${label}: `;
            const strong2 = document.createElement('strong');
            strong2.textContent = (key.includes('rate')) ? `${stats[key]}%` : stats[key];
            
            this.appendChildren(li, [strong1, strong2]);
            this.elements.statisticsList.appendChild(li);
        });
    }

	createRankingItem(player, index) {
		const li = this.createListItem('list-group-item d-flex justify-content-between align-items-center');
	
		const playerInfoDiv = this.createDiv('d-flex align-items-center');
	
		// Add the ranking number
		const number = document.createElement("p");
		number.setAttribute("class", "m-0 me-1");
		number.textContent = `${index + 1}.`;
	
		// Player avatar
		const avatar = document.createElement('img');
		avatar.src = player.player_avatar_url;
		avatar.alt = player.player_nickname;
		avatar.className = 'rounded-circle me-2';
		avatar.style.width = '40px';
		avatar.style.height = '40px';
		avatar.style.objectFit = 'cover';
	
		// Player profile link
		const playerLink = document.createElement('a');
		playerLink.style.textDecoration = 'none';
		playerLink.href = '#';
		playerLink.className = 'ranking_link link-primary fw-bold';
		playerLink.dataset.path = `/profile/${player.player_id}/`;
	
		// Player name
		const playerName = this.createSpan(player.player_username);
		playerLink.appendChild(playerName);
	
		// Calculate win rate percentage
		let winRatePercentage = player.matches_played
			? (player.matches_won / player.matches_played) * 100
			: 0;

		// Format percentage to remove decimals if whole number
		winRatePercentage =
			Number.isInteger(winRatePercentage) ? winRatePercentage.toString() : winRatePercentage.toFixed(2);

		// Display win rate as ratio and percentage
		const winRate = this.createSpan(
			`${player.matches_won || 0}/${player.matches_played || 0} (${winRatePercentage}%)`
		);
	
		// Assemble the ranking item
		this.appendChildren(playerInfoDiv, [number, avatar, playerLink]);
		this.appendChildren(li, [playerInfoDiv, winRate]);
	
		return li;
	}

    createFriendInviteItem(friend, tournament, invitedMap, onInvite) {
        const li = this.createListItem('list-group-item d-flex justify-content-between align-items-center');
        
        const nameSpan = this.createSpan(friend.username);
    
        const isParticipant = tournament.participants.some(
            participant => participant.user_id === friend.user_id
        );
        const isInvited = invitedMap.has(friend.player_profile);
    
        const inviteBtn = this.createButton(
            isInvited ? 'Invited' : 'Invite',
            'btn btn-bd-primary btn-sm action-btn',
            isParticipant || isInvited
        );
    
        if (!isParticipant && !isInvited) {
            inviteBtn.addEventListener('click', async () => {
                //callback `onInvite` pour le lien avec Hubpage
                await onInvite(); 
                inviteBtn.disabled = true;
                inviteBtn.textContent = 'Invited';
            });
        }
    
        this.appendChildren(li, [nameSpan, inviteBtn]);
        return li;
    }

    createHistoryItem(type, entry, currentUserId, historyType) {
        const li = document.createElement('li');
        li.className = 'list-group-item'; 
    
        const nameDiv = this.createDiv();
        const nameStrong = document.createElement('strong');
        nameStrong.textContent = `${type}: `;
        nameDiv.appendChild(nameStrong);
        nameDiv.appendChild(document.createTextNode(entry.name));
    
        const dateDiv = this.createDiv();
        const dateStrong = document.createElement('strong');
        dateStrong.textContent = 'Date: ';
        dateDiv.appendChild(dateStrong);
        const date = entry.start_time ? formatDateTime(entry.start_time) : "Unknown Date";
        dateDiv.appendChild(document.createTextNode(date));
    
        const statusDiv = this.createDiv();
        const statusStrong = document.createElement('strong');
        statusStrong.textContent = 'Status: ';
        statusDiv.appendChild(statusStrong);
        statusDiv.appendChild(document.createTextNode(entry.status));
    
        const opponentDiv = historyType != "tournaments" ? this.createDiv() : null;
        if (opponentDiv) {
            const opponentStrong = document.createElement('strong');
            opponentStrong.textContent = 'Opponent: ';
            opponentDiv.appendChild(opponentStrong);
            let opponent = null
            if (currentUserId === entry.player1 && entry.player2) {
                opponent = entry.player2;
            } else if (currentUserId === entry.player2 && entry.player1) {
                opponent = entry.player1;
            }
            if (opponent) {
                getUserInfo(opponent)
                    .then((finalOpponent) => {
                        opponentDiv.appendChild(document.createTextNode(finalOpponent.nickname));
                    })
            } else {
                opponentDiv.appendChild(document.createTextNode("Unknown"));
            }
        }

        const winnerDiv = this.createDiv();
        const winnerStrong = document.createElement('strong');
        winnerStrong.textContent = 'Winner: ';
        winnerDiv.appendChild(winnerStrong);
        let winner = "No winner yet";
        if (entry.winner) {
            winner = entry.winner.nickname;
        }       
        winnerDiv.appendChild(document.createTextNode(winner));
    
        // Filter out null or undefined elements
        const children = [nameDiv, dateDiv, statusDiv, opponentDiv, winnerDiv].filter(child => child != null);
        this.appendChildren(li, children);
    
        return li;
    }
}

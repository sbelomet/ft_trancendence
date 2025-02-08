import { BaseDOMManager } from "./BaseDOMManager.js";
import { formatDateTime, getUserInfo } from "../../utils/functions_utils.js";

export class ProfileDOMManager extends BaseDOMManager {
    constructor() {
		super();  //le constructeur de BaseDOMManager
        this.initializeElements();
    }

    initializeElements() {
        this.elements = {
            profileName: document.getElementById("profile_name"),
            profileAvatar: document.getElementById("profile_avatar"),
            profileNickname: document.getElementById("profile_nickname"),
            
            // Boutons
            playerRankingBtn: document.getElementById("player_ranking_btn"),
            playerFriendsBtn: document.getElementById("player_friends_btn"),
            viewBlockedBtn: document.getElementById("view_blocked_btn"),
            addFriendBtn: document.getElementById("add_friend_btn"),
            acceptFriendBtn: document.getElementById("accept_friend_btn"),
            blockUserBtn: document.getElementById("block_user_btn"),
            unblockUserBtn: document.getElementById("unblock_user_btn"),

            // Listes et compteurs
            rankingList: document.getElementById("ranking_list"),
            matchHistoryList: document.getElementById("match_history_list"),
            tournamentHistoryList: document.getElementById("tournament_history_list"),
            friendsList: document.getElementById("friends_list"),
            blockedUsersList: document.getElementById("blockedUsersList"),

            // Stats
            playerRanking: document.getElementById("player_ranking"),
            victoriesCount: document.getElementById("victories_count"),
            defeatsCount: document.getElementById("defeats_count"),
            gamesPlayedCount: document.getElementById("games_played_count")
        };
    }

    updateProfile(player) {
        if (this.elements.profileName) {
            this.elements.profileName.textContent = player.user.username;
        }
        if (this.elements.profileNickname) {
            this.elements.profileNickname.textContent = `Nickname: ${player.nickname}`;
        }
        if (this.elements.profileAvatar) {
            this.elements.profileAvatar.src = player.user.avatar || '/media/avatars/default.jpg';
        }
    }

    updateStatistics(data) {
		// 1) #victories_count
        if (this.elements.victoriesCount) {
            this.elements.victoriesCount.textContent = data.matches_won ?? "--";
        }
        if (this.elements.defeatsCount) {
			// 2) #defeats_count
            this.elements.defeatsCount.textContent = data.matches_lost ?? "--";
        }
        if (this.elements.gamesPlayedCount) {
			// 3) #games_played_count
            this.elements.gamesPlayedCount.textContent = data.matches_played ?? "--";
        }
    }


	createRankingItem(player) {
		const li = this.createListItem('list-group-item d-flex justify-content-between align-items-center');
		
		const playerInfoDiv = this.createDiv('d-flex align-items-center');
		
		// Avatar
		//console.log("player in ranking", player);
		//console.log("user info", player.player_username);
		const avatar = document.createElement('img');
		avatar.src = player.player_avatar_url;
		avatar.alt = player.player_nickname;
		avatar.className = 'rounded-circle me-2';
		avatar.style.width = '40px';
		avatar.style.height = '40px';
		avatar.style.objectFit = 'cover';
	
		// Profile link
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
		this.appendChildren(playerInfoDiv, [avatar, playerLink]);
		this.appendChildren(li, [playerInfoDiv, winRate]);
	
		return li;
	}


    createHistoryItem(type, entry, currentUserId, historyType) {
        const li = this.createListItem();
        
        // Name
        const nameDiv = this.createDiv();
        const nameStrong = document.createElement('strong');
        nameStrong.textContent = 'Name: ';
        nameDiv.appendChild(nameStrong);
        nameDiv.appendChild(document.createTextNode(entry.name));

        // Date
        const dateDiv = this.createDiv();
        const dateStrong = document.createElement('strong');
        dateStrong.textContent = 'Date: ';
        dateDiv.appendChild(dateStrong);
        const date = entry.start_time ? formatDateTime(entry.start_time) : "Unknown";
        dateDiv.appendChild(document.createTextNode(date));

        // Status
        const statusDiv = this.createDiv();
        const statusStrong = document.createElement('strong');
        statusStrong.textContent = 'Status: ';
        statusDiv.appendChild(statusStrong);
        statusDiv.appendChild(document.createTextNode(entry.status));

        // Opponent
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
            //console.log(`User: ${currentUserId}, Opponent : ${opponent}, player1: ${entry.player1}, player2: ${entry.player2}`)
            if (opponent) {
                getUserInfo(opponent)
                .then((finalOpponent) => {
                    //console.log(`Final opponent: ${finalOpponent}, username: ${finalOpponent.nickname}`)
                    if (type === "Match")
                        opponentDiv.appendChild(document.createTextNode(finalOpponent.nickname));
                    else
                        opponentDiv.appendChild(document.createTextNode(finalOpponent.username));
                })
            } else {
                opponentDiv.appendChild(document.createTextNode("Unknown"));
            }
        }

        // Winner
        const winnerDiv = this.createDiv();
        const winnerStrong = document.createElement('strong');
        winnerStrong.textContent = 'Winner: ';
        winnerDiv.appendChild(winnerStrong);
        let winner = "No winner yet";
        if (entry.winner) {
            if (type === "Match")
                winner = entry.winner.user.username;
            else 
                winner = entry.winner.nickname;
        }       
        winnerDiv.appendChild(document.createTextNode(winner));

        // Filter out null or undefined elements
        const children = [nameDiv, dateDiv, statusDiv, opponentDiv, winnerDiv].filter(child => child != null);
        this.appendChildren(li, children);
        return li;
    }

    createUserListItem(user, onClickCallback) {
        const li = this.createListItem('list-group-item d-flex justify-content-between align-items-center');
        
        const userInfoDiv = this.createDiv('d-flex align-items-center');
        
        // Avatar
        const avatar = document.createElement('img');
        avatar.src = user.avatar || '/media/avatars/default.jpg';
        avatar.alt = user.username;
        avatar.className = 'rounded-circle me-2';
        avatar.style.width = '40px';
        avatar.style.height = '40px';
        avatar.style.objectFit = 'cover';

        // Lien
        const userLink = document.createElement('a');
		userLink.style.textDecoration = 'none';
        userLink.href = '#';
        userLink.className = 'link_to link-primary fw-bold';
        userLink.dataset.path = `/profile/${user.id}/`;
        
        // Callback de navigation
        if (onClickCallback) {
            userLink.addEventListener('click', (event) => {
                event.preventDefault();
                onClickCallback(userLink.dataset.path);
            });
        }

        // Nom
        const userName = this.createSpan(user.username);
        userLink.appendChild(userName);

        this.appendChildren(userInfoDiv, [avatar, userLink]);
        this.appendChildren(li, [userInfoDiv]);

        return li;
    }

    showButton(button) {
        if (button) {
            button.style.display = "inline-block";
        }
    }

    updateAddFriendButton(text, isDisabled = false) {
        const addFriendBtn = this.elements.addFriendBtn;
        if (!addFriendBtn) return;

        addFriendBtn.textContent = text;
        addFriendBtn.disabled = isDisabled;
        addFriendBtn.classList.toggle("btn-disabled", isDisabled);
    }
}

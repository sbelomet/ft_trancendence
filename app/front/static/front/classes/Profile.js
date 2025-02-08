import { GET, POST_JSON } from "../api.js";
import managerState from "./ManagerState.js";
import { colorToast, endpoints } from "../utils/utils.js";
import { sendFriendRequestNotification } from "../handle_chat.js";
import { ProfileDOMManager } from "./DOM_classes/ProfileDOMManager.js";
import { getUserInfo } from "../utils/functions_utils.js";
import managerStatus from "./ManagerStatus.js";
import managerToast from "./ManagerToast.js";

//Si a un moment plus besoin de destroyer pour avoir un return sur les profils
//simplifier addEventListeners() et addRankingEventListeners()
export default class Profile {
    constructor(ProfileId) {
        this.ProfileId = Number(ProfileId);
        this.isUnmounted = false;
        this.eventListeners = [];
        this.domManager = new ProfileDOMManager();
        
        this.createBlockedUsersCanvas = null;
        this.createFriendsCanvas = null;
        this.createRankingCanvas = null;
    }

    async init() {
        this.isUnmounted = false;

        //console.log("Initializing profile...");
        //console.log("ProfileId:", this.ProfileId);
        //console.log("ManagerState UserID:", managerState.getUserID);

        // 1) réinitialiser l'ui pour éviter les erreurs de boutons
        this.resetUI();

        // 2) récupérer le player
        this.player = await this.fetchPlayerProfile(this.ProfileId);
        //console.log("fetched player:", this.player);

        if (!this.player)
            return;

        // 3) màj du DOM (nom, avatar...)
        this.domManager.updateProfile(this.player);

        // 4) mise en place de la logique d'affichage des boutons
        if (managerState.getUserID !== this.ProfileId) {
			// ...a) si c'est le profile d'un autre user
            const profileStatus = await this.profileStatus();
            //console.log("Viewing profile...", this.ProfileId);

            //this.hideAllButtons();  // masque tout par défaut
			this.domManager.showButton(this.domManager.elements.playerRankingBtn);

            switch (profileStatus) {
                case "blocked":
                    //console.log("User is blocked. Showing unblock button...");
                    this.domManager.showButton(this.domManager.elements.unblockUserBtn);
                    break;
                case "friend":
                    //console.log("User is friend. Showing friend + block...");
                    this.domManager.showButton(this.domManager.elements.playerFriendsBtn);
                    this.domManager.showButton(this.domManager.elements.blockUserBtn);
                    break;
                case "pending":
                    //console.log("Pending friend request. Showing accept friend button...");
                    this.domManager.showButton(this.domManager.elements.acceptFriendBtn);
					this.domManager.showButton(this.domManager.elements.blockUserBtn);
                    break;
                case "user":
                    //console.log("Not a friend. Show addFriend + block...");
                    this.domManager.showButton(this.domManager.elements.addFriendBtn);
                    this.domManager.showButton(this.domManager.elements.blockUserBtn);
                    break;
                case "sent":
                    //console.log("Sent friend req. Show 'Friend Request Sent' + block...");
                    this.domManager.updateAddFriendButton("Friend Request Sent", true);
                    this.domManager.showButton(this.domManager.elements.addFriendBtn);
                    this.domManager.showButton(this.domManager.elements.blockUserBtn);
                    break;
                default:
                    //console.log("Profile status:", profileStatus, "(no buttons available)");
                    break;
            }
        } else {
            //this.hideAllButtons();
            this.domManager.showButton(this.domManager.elements.viewBlockedBtn);
            this.domManager.showButton(this.domManager.elements.playerFriendsBtn);
			this.domManager.showButton(this.domManager.elements.playerRankingBtn);

            // ne pas montrer "Add friend" / "Accept" 
            if (this.domManager.elements.addFriendBtn) {
                this.domManager.elements.addFriendBtn.style.display = "none";
            }
            if (this.domManager.elements.acceptFriendBtn) {
                this.domManager.elements.acceptFriendBtn.style.display = "none";
            }

            // ajouter le canva pour les bloqués:
            this.createBlockedUsersCanvas = new bootstrap.Offcanvas(document.getElementById("blockedUsersCanvas"));
        }

        // 5)ajouter de tous les canvas nécessaires
        this.createRankingCanvas = new bootstrap.Offcanvas(document.getElementById("createRankingCanvas"));
        this.createFriendsCanvas = new bootstrap.Offcanvas(document.getElementById("createFriendsCanvas"));

        // 6) Charger les données (classements, stats, histories, etc.)
        await Promise.all([
            this.fetchStatistics(),
            this.fetchMatchHistory(),
            this.fetchTournamentHistory()
        ]);
        //console.log("Data loaded for profile...", this.ProfileId);
        // 7) Ajouter les listeners
        this.addEventListeners();
    }

	//delete le profile pour éviter les collisions avec le return du navigateur
    destroy() {
        //console.log(`Destroying profile ${this.ProfileId}`);
		// flag instance “unmounted”
        this.isUnmounted = true;

        // loop pour retirer les listeners stockés
        this.eventListeners.forEach(({ element, eventType, handler }) => {
            element.removeEventListener(eventType, handler);
        });
        this.eventListeners = [];

        // Fermer les canvas
        this.createFriendsCanvas?.hide();
        this.createBlockedUsersCanvas?.hide();
        this.createRankingCanvas?.hide();
    }

	// Permet de réinitialiser le boutons, surtout utils pour les return du navigateur
	// pour les boutons bloqués par exemple (galéré à trouver ces solutions)
    resetUI() {
        const {
            playerRankingBtn,
            playerFriendsBtn,
            viewBlockedBtn,
            addFriendBtn,
            acceptFriendBtn,
            blockUserBtn,
            unblockUserBtn
        } = this.domManager.elements;

        if (playerRankingBtn) playerRankingBtn.style.display = "none";
        if (playerFriendsBtn) playerFriendsBtn.style.display = "none";
        if (viewBlockedBtn) viewBlockedBtn.style.display = "none";
        if (addFriendBtn) addFriendBtn.style.display = "none";
        if (acceptFriendBtn) acceptFriendBtn.style.display = "none";
        if (blockUserBtn) blockUserBtn.style.display = "none";
        if (unblockUserBtn) unblockUserBtn.style.display = "none";
    }

    hideAllButtons() {
        const {
            unblockUserBtn,
            playerFriendsBtn,
            blockUserBtn,
            acceptFriendBtn,
            addFriendBtn
        } = this.domManager.elements;

        [unblockUserBtn, playerFriendsBtn, blockUserBtn, acceptFriendBtn, addFriendBtn]
            .forEach(btn => { if (btn) btn.style.display = "none"; });
    }

	// fonction devenue très lourde à cause des returns du navigateur et incohérences de profiles
	// reprendre la première version (en bas du fichier) si autre moyen de s'assure de la cohérence
	//en gros, on ajoute au tableau tous les listeners pour pouvoir les delete quand on destroy
	//et évite que des listener d'un profile précédement consulté agissent sur les actions du profile retourné
    addEventListeners() {
        const {
            addFriendBtn,
            acceptFriendBtn,
            viewBlockedBtn,
            blockUserBtn,
            unblockUserBtn
        } = this.domManager.elements;

        document.getElementById("createRankingCanvas")
		.addEventListener('show.bs.offcanvas', async () => {
			this.fetchPlayerRanking();
		});

        document.getElementById("createFriendsCanvas")
		.addEventListener('show.bs.offcanvas', async () => {
			this.fetchFriends();
		});

        document.getElementById("blockedUsersCanvas")
		.addEventListener('show.bs.offcanvas', async () => {
			this.fetchBlocked();
		});

        // ADD FRIEND
        if (addFriendBtn) {
            const addFriendHandler = async (evt) => {
                evt.preventDefault();
                await this.addFriend();
            };
            addFriendBtn.addEventListener("click", addFriendHandler);
            this.eventListeners.push({ element: addFriendBtn, eventType: "click", handler: addFriendHandler });
        }

        // ACCEPT FRIEND * TO DO, currently used only to notify if there is a pending friend request from the profile we are visitingq
        if (acceptFriendBtn) {
            const acceptFriendHandler = async (evt) => {
                evt.preventDefault();
                // alert("Pending friend request from this user, check your notifications!");
                managerToast.makeToast({
                    message: "Pending friend request from this user, check your notifications!",
                    clickable: false,
                    toast_color: colorToast.blue
                });
            };
            acceptFriendBtn.addEventListener("click", acceptFriendHandler);
            this.eventListeners.push({ element: acceptFriendBtn, eventType: "click", handler: acceptFriendHandler });
        }

        // UNBLOCK
        if (unblockUserBtn) {
            const unblockHandler = async (evt) => {
                evt.preventDefault();
                await this.unblockUser();
            };
            unblockUserBtn.addEventListener("click", unblockHandler);
            this.eventListeners.push({ element: unblockUserBtn, eventType: "click", handler: unblockHandler });
        }

        // BLOCK
        if (blockUserBtn) {
            const blockHandler = async (evt) => {
                evt.preventDefault();
                await this.blockUser();
            };
            blockUserBtn.addEventListener("click", blockHandler);
            this.eventListeners.push({ element: blockUserBtn, eventType: "click", handler: blockHandler });
        }
    }

    async fetchPlayerProfile(playerId) {
        const response = await GET(endpoints.playerDetails(playerId));
        if (!response.ok){
            managerStatus.handleErrorResponse(response.status, response.data.detail, false);
            return null;
        }
        return (response.data);
    }

    async profileStatus() {
        try {
            const response = await GET(`${endpoints.userDetails(this.ProfileId)}status/`);
            return response.data.profile_status; // e.g. "blocked", "friend", "pending", ...
        } catch (error) {
            console.error("Error checking the profile status:", error);
            return false;
        }
    }

	async fetchPlayerRanking() {
		try {
			const response = await GET(endpoints.ranking);
            if (!response.ok) {
                managerStatus.handleErrorResponse(response.status, response.data);
            }
			const rankings = response.data;
	
			// Sort players by win rate, matches played, and username
			const sortedRankings = [...rankings].sort((a, b) => {
				const winRateA = a.matches_played ? a.matches_won / a.matches_played : 0;
				const winRateB = b.matches_played ? b.matches_won / b.matches_played : 0;
	
				// Sort by win rate (descending)
				if (winRateB !== winRateA) {
					return winRateB - winRateA;
				}
	
				// Tie-breaker 1: Sort by matches played (ascending)
				if (a.matches_played !== b.matches_played) {
					return a.matches_played - b.matches_played;
				}
	
				// Tie-breaker 2: Sort alphabetically by username
				return a.player_username.localeCompare(b.player_username);
			});
	
			// Find the rank of the current player
			const playerRanking = sortedRankings.findIndex(r => r.player_id === this.player.id) + 1;
	
			// Update the player's rank in the UI
			if (this.domManager.elements.playerRanking) {
				this.domManager.elements.playerRanking.textContent = `Your rank: ${playerRanking ? playerRanking : "Unranked"}`;;
			}
	
			// Clear the ranking list in the UI
			this.domManager.clearList(this.domManager.elements.rankingList);
	
			// Render the sorted rankings
			sortedRankings.forEach((player) => {
				// Calculate win rate percentage
				const winRatePercentage = player.matches_played
					? ((player.matches_won / player.matches_played) * 100).toFixed(2)
					: 0;
	
				// Create ranking item with percentage
				const rankingItem = this.domManager.createRankingItem(player, winRatePercentage);
				this.domManager.elements.rankingList.appendChild(rankingItem);
			});
	
			// Add event listeners to ranking links
			this.addRankingEventListeners();
		} catch (error) {
			console.error("Error fetching player ranking:", error);
			this.domManager.createErrorMessage(this.domManager.elements.rankingList, "rankings");
		}
  }

    addRankingEventListeners() {
        //aussi devenu lourd pour la cohérence, reprendre le plus simple si changement
        const rankingLinks = document.querySelectorAll(".ranking_link");
        rankingLinks.forEach(link => {
            const rankingLinkHandler = (event) => {
                event.preventDefault();
                const path = link.dataset.path;
                
                // Fermer les canvas
                this.createRankingCanvas?.hide();
                this.createFriendsCanvas?.hide();
                this.createBlockedUsersCanvas?.hide();

                // Charger la page
                managerState.loadFragmentPage(path);
            };
            link.addEventListener("click", rankingLinkHandler);

            // stocker pour clean up
            this.eventListeners.push({
                element: link,
                eventType: "click",
                handler: rankingLinkHandler
            });
        });
    }

    async fetchStatistics() {
        try {
            const response = await GET(endpoints.profileStatistics(this.player.id));
            const data = response.data;
            //console.log("Statistics response:", data);

            if (data) {
                this.domManager.updateStatistics(data);
            } else {
                console.error("Unexpected response structure:", data);
            }
        } catch (error) {
            console.error("Error fetching statistics:", error);
        }
    }

    async fetchMatchHistory() {
        await this.fetchHistory("Match", "matchHistoryList", "matches");
    }

    async fetchTournamentHistory() {
        await this.fetchHistory("Tournament", "tournamentHistoryList", "tournaments");
    }


	async fetchHistory(type, listId, historyType) {
		try {
			const response = await GET(endpoints.history(this.player.id, historyType));
			const data = response.data;
            //console.log(`${type} History Response:`, data);
	
			// Filtrer avoir que le statut "completed"
			const completedData = Array.isArray(data) 
				? data.filter(entry => entry.status === 'completed') 
				: [];
	
			const listElement = this.domManager.elements[listId];
			this.domManager.clearList(listElement);
	
			if (completedData.length === 0) {
				this.domManager.createEmptyMessage(listElement, `${type}`);
				return;
			}
	
			completedData.forEach(entry => {
                const historyItem = this.domManager.createHistoryItem(type, entry, this.ProfileId, historyType);
                listElement.appendChild(historyItem);
			});
		} catch (error) {
			console.error(`Error fetching ${type.toLowerCase()} history:`, error);
			this.domManager.createErrorMessage(this.domManager.elements[listId], `${type.toLowerCase()} history`);
		}
	}

    async fetchFriends() {
        await this.fetchRelations(this.ProfileId, "friend_friends", "friendsList");
    }
    
    async fetchBlocked() {
        if (managerState.getUserID !== this.ProfileId) {
            //console.log("Not the owner, no fetchBlocked call");
            return;
        }
        await this.fetchRelations(this.ProfileId, "blocked_users", "blockedUsersList");
    }

    async fetchRelations(userId, relationType, listElementId) {
        const listElement = this.domManager.elements[listElementId];
        this.domManager.clearList(listElement);

        const loadingItem = this.domManager.createListItem();
        loadingItem.textContent = 'Loading...';
        listElement.appendChild(loadingItem);

        try {
            const endpoint = `${endpoints.userDetails(userId)}see_${relationType}/`;
            const response = await GET(endpoint);
            const data = response.data;

            if (this.isUnmounted) {
                //console.log(`Profile ${this.ProfileId} is unmounted. Ignoring fetched data.`);
                return;
            }

            //console.log(`${relationType} fetched:`, data);
            this.domManager.clearList(listElement);

            if (!Array.isArray(data) || data.length === 0) {
                this.domManager.createEmptyMessage(listElement, 'user');
                return;
            }

            // Callback pour naviguer
            const handleUserClick = (path) => {
                this.createFriendsCanvas?.hide();
                this.createBlockedUsersCanvas?.hide();
                this.createRankingCanvas?.hide();
                managerState.loadFragmentPage(path);
            };

            data.forEach(relation => {
                const userItem = this.domManager.createUserListItem(relation, handleUserClick);
                listElement.appendChild(userItem);
            });
        } catch (error) {
            console.error(`Error fetching ${relationType}:`, error);
            this.domManager.createErrorMessage(listElement, relationType);
        }
    }

	async addFriend() {
		// try {
        const response = await POST_JSON({ to_user: this.ProfileId }, endpoints.friendships);
        //console.log("Friend request sent:", response);
        if (!response.ok) {
            managerStatus.handleErrorResponse(response.status, response.data, false);
            return;
        }
        sendFriendRequestNotification(this.player, response.data);
        // màj du bouton AddFriend
        this.domManager.updateAddFriendButton("Friend Request Sent", true);
		// } catch (error) {
		// 	console.error("Error sending friend request:", error);
		// 	alert("Failed to send friend request. Please try again.");
		// }
	}
	
	async isFriend() {
		// try {
        const response = await GET(`${endpoints.userDetails(managerState.getUserID)}see_friend_friends/`);
        if (!response.ok) {
            managerStatus.handleErrorResponse(response.status, response.data, false);
            return;
        }
        const friends = response.data;
        return friends.some(friend => Number(friend.id) === this.ProfileId);
		// } catch (error) {
		// 	console.error("Error checking friendship:", error);
		// 	return false;
		// }
	}

    async blockUser() {
        // try {
        const response = await POST_JSON({}, `${endpoints.friendships}${this.ProfileId}/block/`);
        //console.log("User blocked:", response);
        if (!response.ok) {
            managerStatus.handleErrorResponse(response.status, response.data, false);
            return;
        }
        // alert("User has been blocked.");
        managerToast.makeToast({
            message: "User has been blocked.",
            clickable: false,
            toast_color: colorToast.green
        });

        // masquer le bouton block
        const { blockUserBtn } = this.domManager.elements;
        if (blockUserBtn) blockUserBtn.style.display = "none";

        // rafraîchir l’état
        this.updateButtons();
        // } catch (error) {
        //     console.error("Error blocking user:", error);
        //     alert("Failed to block user. Please try again.");
        // }
    }

    async unblockUser() {
        // try {
        const response = await POST_JSON({}, `${endpoints.friendships}${this.ProfileId}/unblock/`);
        //console.log("User unblocked:", response);
        if (!response.ok) {
            managerStatus.handleErrorResponse(response.status, response.data, false);
            return;
        }
        // alert("User has been unblocked.");
        managerToast.makeToast({
            message: "User has been unblocked.",
            clickable: false,
            toast_color: colorToast.green
        });

        // réinitialiser le bouton addFriend
        this.domManager.updateAddFriendButton("Friend Request", false);

        // rafraîchir l’état
        this.updateButtons();
        // } catch (error) {
        //     console.error("Error unblocking user:", error);
        //     alert("Failed to unblock user. Please try again.");
        // }
    }

    async updateButtons() {
        const status = await this.profileStatus();
        // Fermer les canvas si besoin
        this.createFriendsCanvas?.hide();
        this.createBlockedUsersCanvas?.hide();
        this.createRankingCanvas?.hide();

        this.hideAllButtons();

        const {
            unblockUserBtn,
            blockUserBtn,
            addFriendBtn,
            acceptFriendBtn,
            playerFriendsBtn
        } = this.domManager.elements;

        switch (status) {
            case "blocked":
                //console.log("User is blocked. Updating buttons...");
                this.domManager.showButton(unblockUserBtn);
                break;
            case "pending":
                //console.log("A pending friend request. Updating buttons...");
                this.domManager.showButton(acceptFriendBtn);
                break;
            case "friend":
                //console.log("User is a friend. Updating buttons...");
                this.domManager.showButton(blockUserBtn);
                this.domManager.showButton(playerFriendsBtn);
                break;
            case "user":
                //console.log("User is not a friend. Updating buttons...");
                this.domManager.showButton(blockUserBtn);
                this.domManager.showButton(addFriendBtn);
                break;
            default:
                //console.log("User is blocking us or unknown status. No buttons available...");
                break;
        }
    }
}

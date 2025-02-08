import { GET, POST_JSON } from "../api.js";
import managerState from "./ManagerState.js";
import { endpoints, colorToast } from "../utils/utils.js";
import managerGame from "./game_classes/ManagerGame.js";
import { HubDOMManager } from "./DOM_classes/HubDOMManager.js";
import { sendInviteNotification, sendTourneyInviteNotification } from "../handle_chat.js";
import managerStatus from "./ManagerStatus.js";
import managerToast from "./ManagerToast.js";

export default class HubPage {
    constructor() {
        this.domManager = new HubDOMManager();
		this.canvas = this.getCanvas();
        this.currentUser = null;
        this.currentTournamentId = null;
    }

	getCanvas() {
        return {
            createGame: new bootstrap.Offcanvas(document.getElementById("createGameCanvas")),
            createTournament: new bootstrap.Offcanvas(document.getElementById("createTournamentCanvas")),
            createRanking: new bootstrap.Offcanvas(document.getElementById("createRankingCanvas")),
            createInvitation: new bootstrap.Offcanvas(document.getElementById("createGameInvitationCanvas")),
			createTourInvitation: new bootstrap.Offcanvas(document.getElementById("createInvitationCanvas"))
        };
    }

    async init() {
		const user = await this.fetchCurrentUser();
		if (user === undefined)
			return ;
		else
			this.currentUser = user;

        await Promise.all([
            this.fetchGames(),
            this.fetchTournaments(),
            this.fetchStatistics(),
            this.fetchMatchHistory(),
            this.fetchTournamentHistory()
        ]);

        this.addEventListeners();
    }

    async fetchCurrentUser() {
        // try {
			const response = await GET(endpoints.userDetails("me"));
			if (!response.ok) {
				managerStatus.handleErrorResponse(response.status, response.data, false);
				return (undefined);
			} else
            	return (response.data);
        // } catch (error) {
        //     console.error("Error fetching current user:", error);
        //     return null;
        // }
    }

    addEventListeners() {
		document.getElementById('createGameCanvas')
		.addEventListener('hide.bs.offcanvas', () => {
			document.getElementById("create_game_form").reset();
		});
	
		document.getElementById('createTournamentCanvas')
		.addEventListener('hide.bs.offcanvas', () => {
			document.getElementById("create_tournament_form").reset();
		});

		document.getElementById("createRankingCanvas")
		.addEventListener('show.bs.offcanvas', async () => {
			await this.fetchRankings();
		});

		const historical = document.getElementById('offcanvasHistorical')
		historical.addEventListener('show.bs.offcanvas', () => {
			const element = document.getElementById("historical_wrapper");
			const element2 = document.getElementById("tournament_history_wrap");
			element.classList.remove("row");
			element2.classList.add("mt-2");
		})
		historical.addEventListener('hide.bs.offcanvas', () => {
			const element = document.getElementById("historical_wrapper");
			const element2 = document.getElementById("tournament_history_wrap");
			element.classList.add("row");
			element2.classList.remove("mt-2");
		})

		document.getElementById("create_game_form")?.addEventListener(
			"submit", 
			this.handleGameFormSubmit.bind(this)
		);
		
		document.getElementById("create_tournament_form")?.addEventListener(
			"submit", 
			this.handleTournamentFormSubmit.bind(this)
		);
	
		document.getElementById("withdraw_tournament_btn")?.addEventListener(
			"click", 
			() => this.currentTournamentId && this.withdrawTournament(this.currentTournamentId)
		);
	}

	async withdrawTournament(tournamentId) {
		// try {
		const response = await POST_JSON({}, endpoints.withdrawTournament(tournamentId));
		if (!response.ok) {
            managerStatus.handleErrorResponse(response.status, response.data, false);
            return;
        }

		await this.fetchTournaments();
		document.getElementById("tourney-close-btn").click();
		// } catch (error) {
		// 	console.error(`Failed to withdraw tournament ${tournamentId}:`, error);
		// 	alert("Error while withdrawing from the tournament.");
		// }
	}

    async handleGameFormSubmit(event) {
        event.preventDefault();
        event.stopPropagation();

        const formData = {
            name: document.getElementById('game_name')?.value.trim(),
            gameType: document.getElementById('game_type')?.value,
            rounds: document.getElementById('game_rounds')?.value.trim()
        };

        if (!this.validateGameForm(formData)) return;

        const data = {
            name: formData.name,
            game_type: formData.gameType,
            rounds_needed: formData.rounds
        };

        await this.submitGameForm(data);
    }

    validateGameForm(data) {
        if (!data.name || !data.gameType || !data.rounds) {
            // alert("Please fill out all fields.");
			managerToast.makeToast({
				message: "Please fill out all fields.",
				clickable: false,
				toast_color: colorToast.blue
			});
            return false;
        }
        if (isNaN(data.rounds) || data.rounds < 1 || data.rounds > 20) {
            // alert("Number of rounds must be at least 1 and max 20.");
			managerToast.makeToast({
				message: "Number of rounds must be at least 1 and max 20.",
				clickable: false,
				toast_color: colorToast.blue
			});
            return false;
        }
        return true;
    }

	async submitGameForm(data) {
		const response = await managerGame.createNewGame(data);
		// console.log("Game created: ", response);

		const span = document.getElementById("createGameSpan");
		if (response.ok) {
			span.classList.add("bg-success");
			span.textContent = "Game successfuly created";
			if (response.game_type === "remote")
				await managerGame.initGame(response.url, response.game_type);
		} else {
			span.classList.add("bg-danger");
			span.textContent = response.message.name;
		}

		span.classList.remove("visually-hidden");

		setTimeout(() => {
			span.textContent = "";
			span.classList.add("visually-hidden");
			if (!response.ok)
				span.classList.remove("bg-danger");
			else {
				span.classList.remove("bg-success");
				this.canvas.createGame.hide();
			}
		}, 2500);

		await this.fetchGames();
	}

    async handleTournamentFormSubmit(event) {
        event.preventDefault();
        event.stopPropagation();

        const formData = {
            name: document.getElementById('tournament_name')?.value.trim(),
            description: document.getElementById('tournament_description')?.value,
            maxPlayers: document.getElementById('max_player')?.value.trim(),
            startInterval: parseInt(document.getElementById('tournament_start_interval')?.value, 10)
        };

        if (!this.validateTournamentForm(formData)) return;

    	const roundedTime = new Date();
		if (roundedTime.getSeconds() > 50)
			roundedTime.setMinutes(roundedTime.getMinutes() + 1);
		roundedTime.setSeconds(0, 0);
		// Add the selected interval (in minutes) to the rounded time
		const startDate = new Date(roundedTime.getTime() + formData.startInterval * 60 * 1000);

        const data = {
			name: formData.name,
            description: formData.description,
            max_players: parseInt(formData.maxPlayers),
            start_time: startDate.toISOString()
        };

        await this.submitTournamentForm(data);
    }

    validateTournamentForm(data) {
        if (!data.name || !data.maxPlayers || !data.startInterval) {
            // alert("Please fill out all the required fields.");
			managerToast.makeToast({
				message: "Please fill out all the required fields.",
				clickable: false,
				toast_color: colorToast.blue
			});
            return false;
        }
        if (isNaN(data.maxPlayers) || data.maxPlayers < 3 || data.maxPlayers > 20) {
            // alert("Number of players must be at least 3 and max 20.");
			managerToast.makeToast({
				message: "Number of players must be at least 3 and max 20.",
				clickable: false,
				toast_color: colorToast.blue
			});
            return false;
        }
        if (isNaN(data.startInterval) || data.startInterval < 1 || data.startInterval > 5) {
			// alert("Start interval must be between 1 and 5 minutes.");
			managerToast.makeToast({
				message: "Start interval must be between 1 and 5 minutes.",
				clickable: false,
				toast_color: colorToast.blue
			});
            return false;
        }
        return true;
    }

    async submitTournamentForm(data) {

		const response = await POST_JSON(data, endpoints.tournaments);

		const span = document.getElementById("createTournamentSpan");
		if (response.ok) {
			span.classList.add("bg-success");
			span.textContent = "Successfuly created";
		} else {
			span.classList.add("bg-danger");
			span.textContent = managerStatus.getMessage(response.data);
		}

		span.classList.remove("visually-hidden");

		setTimeout(() => {
			span.textContent = "";
			span.classList.add("visually-hidden");
			if (!response.ok)
				span.classList.remove("bg-danger");
			else {
				span.classList.remove("bg-success");
				this.canvas.createTournament.hide();
			}
		}, 2500);

		await this.fetchTournaments();
	}

	async fetchGames() {
		try {
			const response = await GET(`${endpoints.games}?status=waiting`);
			
			// console.log("🚀 Fetching games...");
			// console.log("📢 API Response:", response);
	
			if (!response.ok) {
				managerStatus.handleErrorResponse(response.status, response.data, false);
			}
	
			const data = response.data;
			this.domManager.clearList(this.domManager.elements.gamesList);
	
			if (!data.results?.length) {
				// console.warn("⚠️ No games found.");
				this.domManager.createEmptyMessage(this.domManager.elements.gamesList, "Game");
				return;
			}
			// Track how many games actually get appended to the UI
			let appendedCount = 0;

	
			const actions = {
				onJoin: this.joinGame.bind(this),
				onInvite: this.openGameInviteCanvas.bind(this)
			};
	
			data.results.forEach(game => {
				// console.log("🎮 Processing game:", game);
				// console.log("🆔 Current User ID:", this.currentUser.id);
				// console.log("👤 Created by:", game.created_by);
				// console.log("🏆 Game Type:", game.game_type);
				// console.log("📌 Status:", game.status);
	
				if ((game.game_type === 'remote' && game.status === 'waiting') || 
					(game.game_type === 'local' && game.created_by === managerState.getUserID)) {
					
					// console.log("✅ Adding game to UI:", game.id);
					const gameItem = this.domManager.createGameListItem(
						game, 
						this.currentUser.id,
						actions
					);
					this.domManager.elements.gamesList.appendChild(gameItem);
					appendedCount++;
				} else {
					//console.log("❌ Game does not meet conditions for UI:", game.id);
				}
			});

			// If no games were appended, show "No game found."
			if (appendedCount === 0) {
				//console.warn("⚠️ No game found for this user in filtered results.");
				this.domManager.createEmptyMessage(this.domManager.elements.gamesList, "Game");
			}
		} catch (error) {
			console.error("🔥 Error fetching games:", error);
			managerToast.makeToast({
				message: "Error fetching games",
				clickable: false,
				toast_color: colorToast.red
			});
			//this.domManager.createErrorMessage(this.domManager.elements.gamesList, "Game");
		}
	}

    async fetchTournaments() {
        try {
            const response = await GET(`${endpoints.tournaments}?status=upcoming`);
			if (!response.ok) {
				managerStatus.handleErrorResponse(response.status, response.data, false);
			}
            const data = response.data;
			this.domManager.clearList(this.domManager.elements.tournamentsList);

            if (!data.results?.length) {
                this.domManager.createEmptyMessage(this.domManager.elements.tournamentsList, "Tournament");
                return;
            }

            const actions = {
                onJoin: this.joinTournament.bind(this),
                onOptions: this.openInvitationCanvas.bind(this),
                onWithdraw: this.withdrawTournament.bind(this)
            };

            data.results.forEach(tournament => {
                const tournamentItem = this.domManager.createTournamentListItem(
                    tournament,
                    this.currentUser,
                    actions
                );
                this.domManager.elements.tournamentsList.appendChild(tournamentItem);
            });
        } catch (error) {
            console.error("Error fetching tournaments:", error);
            managerToast.makeToast({
				message: "Error fetching tournaments",
				clickable: false,
				toast_color: colorToast.red
			});
			//this.domManager.createErrorMessage(this.domManager.elements.tournamentsList, "Tournament");
        }
    }

//JB TO FIX
	async joinGame(gameId, gameType) {
		try {
			// Step 1: Check if the specific game is interrupted
			const interruptedResponse = await GET(`${endpoints.games}?status=interrupted`);

			if (interruptedResponse && interruptedResponse.data && interruptedResponse.data.results.length > 0) {
				// Check if the interrupted game matches the game the player is trying to join
				const interruptedGame = interruptedResponse.data.results.find(g => g.id === gameId);

				if (interruptedGame) {
					//console.warn(`Cannot join game ${gameId}. It was interrupted.`);
					managerToast.makeToast({
						message: `Cannot join game ${gameId}. It was interrupted.`,
						clickable: false,
						toast_color: colorToast.red
					});
					//this.domManager.createErrorMessage(this.domManager.elements.gamesList, "This game was interrupted and cannot be joined.");
					return;
				}
			}

			const websocketUrl = endpoints.joinGame(gameId, gameType);
			managerGame.initGame(websocketUrl, gameType);

		} catch (error) {
			console.error("Error fetching game status before joining:", error);
			managerToast.makeToast({
				message: "Error fetching game status before joining",
				clickable: false,
				toast_color: colorToast.red
			});
			//this.domManager.createErrorMessage(this.domManager.elements.gamesList, "An error occurred while checking game status. Please try again.");
		}
	}

	async openGameInviteCanvas(item) {
		this.canvas.createInvitation.show();
		const friendsList = document.getElementById('friends_list_game');
		friendsList.innerHTML = '';

		const response = await GET(endpoints.userFriends(this.currentUser.id));
		if (!response.ok) {
			managerStatus.handleErrorResponse(response.status, response.data, false);
		}
		const friends = response.data;
		friends.forEach((friend) => {
			const listItem = document.createElement('li');
			listItem.className = 'list-group-item d-flex justify-content-between align-items-center';
			const friendUsername = document.createElement('span');
			friendUsername.innerText = friend.username;
			listItem.appendChild(friendUsername);

			const inviteBtn = document.createElement('button');
			inviteBtn.className = 'btn btn-bd-primary btn-sm action-btn';
			inviteBtn.textContent = 'Invite';
			
			inviteBtn.addEventListener('click', () => {
				sendInviteNotification(friend, item);
				inviteBtn.disabled = true;
				inviteBtn.textContent = 'Invited';
				this.canvas.createInvitation.hide();
			});

			listItem.appendChild(inviteBtn);
			friendsList.appendChild(listItem);
		});
	}

	addTournamentButtonActions(item, listItem) {
		const isParticipant = item.participants.some(
			(participant) => participant.user_id === this.currentUser.id
		);
		const capacity = item.participants.length < item.max_players;
	
		if (!isParticipant && capacity) {
			const joinBtn = document.createElement('button');
			joinBtn.className = 'btn btn-bd-primary btn-sm action-btn';
			joinBtn.textContent = 'Join';
			joinBtn.addEventListener('click', () => this.joinTournament(item.id));
			listItem.appendChild(joinBtn);
		} else if (isParticipant && capacity) {
			const inviteBtn = document.createElement('button');
			inviteBtn.className = 'btn btn-bd-primary btn-sm action-btn';
			inviteBtn.textContent = 'Options';
			inviteBtn.addEventListener('click', () => this.openInvitationCanvas(item));
			listItem.appendChild(inviteBtn);
		} else if (isParticipant && !capacity) {
			const withdrawBtn = document.createElement('button');
			withdrawBtn.className = 'btn btn-bd-primary btn-sm action-btn';
			withdrawBtn.textContent = 'Withdraw';
			withdrawBtn.addEventListener('click', () => this.withdrawTournament(item.id));
			listItem.appendChild(withdrawBtn);
		}
	}
	
	async joinTournament(tournamentId) {
		// try {
		const response = await POST_JSON({}, endpoints.joinTournament(tournamentId));
		if (!response.ok) {
            managerStatus.handleErrorResponse(response.status, response.data, false);
            return;
        }

		await this.fetchTournaments();
		// } catch (error) {
		// 	console.error(`Failed to join tournament ${tournamentId}:`, error);
		// 	alert("Error joining tournament.");
		// }
	}
	
	async openInvitationCanvas(tournament) {
		try {
			this.currentTournamentId = tournament.id;
		   	this.canvas.createTourInvitation.show();

		   const friendsList = this.domManager.elements.friendsList;
		   if (friendsList) {
			   const loadingDiv = this.domManager.createDiv();
			   loadingDiv.textContent = 'Loading...';
			   friendsList.innerHTML = '';
			   friendsList.appendChild(loadingDiv);
            }
			
            await this.fetchPlayerFriendsForInvite(tournament);
        } catch (error) {
			console.error("Error opening invitation modal:", error);
        }
    }
	
	async fetchStatistics() {
		try {
			const response = await GET(endpoints.statistics);
			if (!response.ok) {
				managerStatus.handleErrorResponse(response.status, response.data, false);
			}
			const data = response.data;
			
			if (data) {
				this.domManager.updateStatistics(data);
			} else {
				throw new Error("Invalid statistics data");
			}
		} catch (error) {
			console.error("Error fetching statistics:", error);
			this.domManager.createErrorMessage(this.domManager.elements.statisticsList, "statistics");
		}
	}
	
	async fetchHistory(type, listId, historyType) {
		try {
			const response = await GET(endpoints.history(this.currentUser.id, historyType));
			if (!response.ok) {
				managerStatus.handleErrorResponse(response.status, response.data, false);
			}
			const data = response.data;
			
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
				const historyItem = this.domManager.createHistoryItem(type, entry, this.currentUser.id, historyType);
				listElement.appendChild(historyItem);
			});
		} catch (error) {
			console.error(`Error fetching ${type.toLowerCase()} history:`, error);
			this.domManager.createErrorMessage(
				this.domManager.elements[listId], 
				`${type.toLowerCase()} history`
			);
		}
	}

	async fetchMatchHistory() {
		await this.fetchHistory("Match", "matchHistoryList", "matches");
	}
	
	async fetchTournamentHistory() {
		await this.fetchHistory("Tournament", "tournamentHistoryList", "tournaments");
	}
	
	async fetchRankings() {
		try {
			const response = await GET(endpoints.ranking);
			if (!response.ok) {
				managerStatus.handleErrorResponse(response.status, response.data, false);
			}
			await this.updateRankingsList(response.data);
		} catch (error) {
			console.error("Error fetching player ranking:", error);
			this.domManager.createErrorMessage(this.domManager.elements.rankingList, "rankings");
		}
	}
	
	async updateRankingsList(rankings) {
		if (!this.domManager.elements.rankingList) {
			console.error("Ranking list element not found.");
			return;
		}
	
		// Create a new sorted array instead of mutating the original
		const sortedRankings = [...rankings].sort((a, b) => {
			const winRateA = a.matches_played ? a.matches_won / a.matches_played : 0;
			const winRateB = b.matches_played ? b.matches_won / b.matches_played : 0;
	
			// Sort by win rate (descending)
			if (winRateB !== winRateA) {
				return winRateB - winRateA;
			}
	
			// Tie-breaker 1: Sort by matches played (ascending, fewer matches come first)
			if (a.matches_played !== b.matches_played) {
				return a.matches_played - b.matches_played;
			}
	
			// Tie-breaker 2: Sort by player username (alphabetical order)
			return a.player_username.localeCompare(b.player_username);
		});
	
		// Clear the ranking list in the DOM
		this.domManager.clearList(this.domManager.elements.rankingList);
	
		// Find and display the current user's rank
		const playerRank = sortedRankings.findIndex(r => r.player_id === this.currentUser.id) + 1;
		const yourRank = document.getElementById("rank_log_player");
		yourRank.textContent = `Your rank: ${playerRank ? playerRank : "Unranked"}`;
	
		// Render the sorted rankings with percentages
		sortedRankings.forEach((player, index) => {
			// Calculate win rate percentage THIS is the one to access for the percent 
			const winRatePercentage = player.matches_played
				? ((player.matches_won / player.matches_played) * 100).toFixed(2) // Round to 2 decimals
				: 0;

			// Create ranking item
			const rankingItem = this.domManager.createRankingItem(player, index, winRatePercentage);
			this.domManager.elements.rankingList.appendChild(rankingItem);
		});
	
		// Reattach ranking event listeners
		this.addRankingEventListeners();
	}
	
	addRankingEventListeners() {
		const rankingLinks = document.querySelectorAll(".ranking_link");
		rankingLinks.forEach(link => {
			link.addEventListener("click", (event) => {
				event.preventDefault();
				const path = link.dataset.path;
				this.canvas.createRanking.hide();
				managerState.loadFragmentPage(path);
			});
		});
	}
	
	async fetchTournamentInvitations(tournamentId) {
		try {
			const response = await GET(endpoints.tournamentDetails(tournamentId));
			if (!response.ok) {
				document.getElementById("tourney-close-btn").click();
				managerStatus.handleErrorResponse(response.status, response.data, false);
			}
			const data = response.data;
			return data.invitations || [];
		} catch (error) {
			console.error(`Error fetching invitations for tournament ${tournamentId}:`, error);
			return [];
		}
	}
	
	async fetchPlayerFriendsForInvite(tournament) {
		try {
			const existingInvitations = await this.fetchTournamentInvitations(tournament.id);
			const invitedMap = new Map(existingInvitations.map(inv => [inv.to_player, true]));
			
			this.domManager.clearList(this.domManager.elements.friendsList);
			
			const response = await GET(endpoints.userFriends(this.currentUser.id));
			if (!response.ok) {
				document.getElementById("tourney-close-btn").click();
				managerStatus.handleErrorResponse(response.status, response.data, false);
			}
			const friends = response.data;
			friends.forEach(friend => {
				const isCreator = friend.id === tournament.created_by.user.id;
            	const isParticipant = tournament.participants.some(participant => participant.user_id === friend.id);
            	const isAlreadyInvited = invitedMap.has(friend.id);

            	// Skip the friend if they are the creator, a participant, or already invited
            	if (isCreator || isParticipant || isAlreadyInvited) {
                	// console.log(`${friend.username} is already involved in the tournament and cannot be invited.`);
                	return;
            	}
            	
				const friendItem = this.domManager.createFriendInviteItem(
					friend,
					tournament,
					invitedMap,
					async () => {
						// callback d’invitation => on appelle inviteToTournament
						await this.inviteToTournament(tournament.id, friend);
					}
				);
				
				this.domManager.elements.friendsList.appendChild(friendItem);
			});
		} catch (error) {
			console.error("Error fetching friends for invite:", error);
			this.domManager.createErrorMessage(this.domManager.elements.friendsList, "friends list");
		}
	}
	
	async inviteToTournament(tournamentId, friend) {
		// try {
		const data = {
			tournament: tournamentId,
			from_player: this.currentUser.player_profile,
			to_player: friend.player_profile
		};
		
		const response = await POST_JSON(data, endpoints.invitations);
		if (!response.ok) {
            managerStatus.handleErrorResponse(response.status, response.data, false);
            return;
        }
		sendTourneyInviteNotification(friend, tournamentId);
		
		// alert("Invitation sent successfully!");
		managerToast.makeToast({
            message: "Invitation sent successfully!",
            clickable: false,
            toast_color: colorToast.green
        });
		// } catch (error) {
		// 	console.error("Error inviting friend to tournament:", error);
			
		// 	if (error.message?.includes("already been invited")) {
		// 		alert(`Error: ${friend.username} has already been invited to this tournament.`);
		// 	} else {
		// 		alert("Failed to send invitation. Please try again later.");
		// 	}
		// }
	}
}
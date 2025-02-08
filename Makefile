# **************************************************************************** #
#                                                                              #
#                                                         :::      ::::::::    #
#    Makefile                                           :+:      :+:    :+:    #
#                                                     +:+ +:+         +:+      #
#    By: mremenar <mremenar@student.42.fr>          +#+  +:+       +#+         #
#                                                 +#+#+#+#+#+   +#+            #
#    Created: 2024/11/13 11:26:28 by lgosselk          #+#    #+#              #
#    Updated: 2025/01/21 10:17:38 by mremenar         ###   ########.fr        #
#                                                                              #
# **************************************************************************** #

# Variables
NAME		=	transcendence
ENTRY_PROD	=	./app/entrypoint.prod.sh
ENTRY_DEV	=	./app/entrypoint.sh

# Colors
RED 		=	\033[1;91m
YELLOW		=	\033[1;93m
GREEN		=	\033[1;92m
DEF_COLOR	=	\033[0;39m

# Commands
all:	$(NAME)

$(NAME):	pre
	@echo "$(GREEN) Starting production in detach $(DEF_COLOR)"
	@docker compose -f docker-compose.prod.yml up -d --build
	@echo "$(YELLOW) Starting migrations $(DEF_COLOR)"
	@sleep 3
	docker compose -f docker-compose.prod.yml exec web python manage.py makemigrations
	docker compose -f docker-compose.prod.yml exec web python manage.py migrate --noinput
	@echo "$(YELLOW) Setting up initial data $(DEF_COLOR)"
	@$(MAKE) setup-data
	@echo "$(YELLOW) Starting collectionStatic $(DEF_COLOR)"
	docker compose -f docker-compose.prod.yml exec web python manage.py collectstatic --no-input --clear
	@echo "$(GREEN) Ready! $(DEF_COLOR)"

no:
	@echo "$(GREEN) Starting production without detach $(DEF_COLOR)"
	@docker compose -f docker-compose.prod.yml up --build
#	Manual migrations and collect statics
#	docker compose -f docker-compose.prod.yml exec web python manage.py migrate --noinput
#	docker compose -f docker-compose.prod.yml exec web python manage.py collectstatic --no-input --clear

dev:
	@echo "$(GREEN) Starting in dev $(DEF_COLOR)"
	@docker compose up --build

test_dev:
	@docker compose exec web python manage.py test 

clean_dev:
	@docker compose down -v
	@echo "$(RED) Removed! $(DEF_COLOR)"

clean:
	@docker compose -f docker-compose.prod.yml down -v
	@echo "$(RED) Removed! $(DEF_COLOR)"

fclean:
	@docker system prune

re_static:
	docker compose -f docker-compose.prod.yml exec web python manage.py collectstatic --no-input --clear
	@echo "$(GREEN) Ready! $(DEF_COLOR)"

pre:
	@chmod +x $(ENTRY_DEV)
	@chmod +x $(ENTRY_PROD)


mig:
	docker compose -f docker-compose.prod.yml exec web python manage.py makemigrations
	docker compose -f docker-compose.prod.yml exec web python manage.py migrate
	@$(MAKE) setup-data
	docker compose -f docker-compose.prod.yml exec web python manage.py collectstatic --no-input --clear

setup-data:
	@echo "$(YELLOW) Setting up initial data $(DEF_COLOR)"
	@docker compose exec web python manage.py setup_data

bash:
	@echo "$(YELLOW) Opening Bash in the web container $(DEF_COLOR)"
	docker compose -f docker-compose.prod.yml exec web /bin/bash

test:
	docker compose -f docker-compose.prod.yml exec web python manage.py test

pytest:
	docker compose -f docker-compose.prod.yml exec web pytest -s server_side_pong/

logs:
	docker compose -f docker-compose.prod.yml logs

watch:
	docker compose -f docker-compose.prod.yml up --watch 
	sh ./migstat.sh

down:
	@docker compose -f docker-compose.prod.yml down

super:
	@echo "$(YELLOW) Opening Bash in the web container $(DEF_COLOR)"
	docker compose -f docker-compose.prod.yml exec web python manage.py create_ad
	
up:
	@docker compose -f docker-compose.prod.yml up
#	Manual migrations and collect statics
	docker compose -f docker-compose.prod.yml exec web python manage.py migrate --noinput
	docker compose -f docker-compose.prod.yml exec web python manage.py collectstatic --no-input --clear		

.PHONY:			all clean_dev clean fclean re_static pre mig dev no_detach setup-data
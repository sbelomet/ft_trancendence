docker-compose -f docker-compose.prod.yml exec web python manage.py  makemigrations
docker-compose -f docker-compose.prod.yml exec web python manage.py migrate --noinput
docker-compose -f docker-compose.prod.yml exec web python manage.py collectstatic --no-input --clear
#docker-compose -f docker-compose.prod.yml exec web pytest -s server_side_pong/
docker-compose -f docker-compose.prod.yml exec web python manage.py create_user
#docker-compose -f docker-compose.prod.yml exec web python manage.py clear_messages
#docker-compose -f docker-compose.prod.yml exec web python manage.py clear_user
#--dependencies
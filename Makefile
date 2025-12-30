run-local:
	docker-compose -f docker-compose-local.yml up -d --build --force-recreate

stop-local:
	docker-compose -f docker-compose-local.yml down -v --remove-orphans

run-staging:
	docker-compose -f docker-compose-staging.yml --env-file .env.example up -d --build --force-recreate
	docker exec -it app bash -c "cd /app/backend && uv run python manage.py migrate"
	docker exec -it app bash -c "cd /app/backend && uv run python manage.py generate_test_data"

stop-staging:
	docker-compose -f docker-compose-staging.yml down -v --remove-orphans
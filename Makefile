run-local:
	docker-compose -f docker-compose-local.yml up -d --build --force-recreate

stop-local:
	docker-compose -f docker-compose-local.yml down -v --remove-orphans
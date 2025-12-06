VENV_DIR = .venv
ACTIVATE_VENV := . $(VENV_DIR)/bin/activate

$(VENV_DIR):
	python3 -m venv $(VENV_DIR)
	$(ACTIVATE_VENV) && pip install --upgrade pip
	$(ACTIVATE_VENV) && pip install --requirement requirements.txt

install: $(VENV_DIR)

# Run black formatter
black: $(VENV_DIR)
	$(ACTIVATE_VENV) && black .

# Run ruff linter
ruff: $(VENV_DIR)
	$(ACTIVATE_VENV) && ruff check .

# Run pytest
pytest: $(VENV_DIR)
	$(ACTIVATE_VENV) && PYTHONPATH=. pytest

# Run all tests (includes black, ruff, and pytest)
test: black ruff pytest

# Docker commands
DOCKER_NETWORK=bot_downloader_network

POSTGRES_VOLUME = postgres_data
POSTGRES_CONTAINER = telegram_bot_postgres_database

RABBITMQ_VOLUME = rabbitmq_data
RABBITMQ_CONTAINER = telegram_bot_rabbitmq

# Автоматически загружаем переменные из .env
include .env
export $(shell sed 's/=.*//' .env)

docker_volumes:
	docker volume create $(POSTGRES_VOLUME) || true
	docker volume create $(RABBITMQ_VOLUME) || true
docker_net:
	docker network create $(DOCKER_NETWORK) || true

# Postgres
postgres_run: docker_volumes docker_net
	docker run -d \
	--name $(POSTGRES_CONTAINER) \
	-e POSTGRES_USER="$(POSTGRES_USER)" \
	-e POSTGRES_PASSWORD="$(POSTGRES_PASSWORD)" \
	-e POSTGRES_DB="$(POSTGRES_DATABASE)" \
	-p "$(POSTGRES_PORT):$(POSTGRES_CONTAINER_PORT)" \
	-v $(POSTGRES_VOLUME):/var/lib/postgresql/data \
	--health-cmd="pg_isready -U $(POSTGRES_USER)" \
	--health-interval=30s \
	--health-timeout=10s \
	--health-retries=5 \
	--network $(DOCKER_NETWORK) \
	docker.io/library/postgres:17

postgres_stop:
	docker stop $(POSTGRES_CONTAINER)
	docker rm $(POSTGRES_CONTAINER)

# Rabbitmq
rabbitmq_run: docker_volumes docker_net
	docker run -d \
	--name $(RABBITMQ_CONTAINER) \
	-e RABBITMQ_USER="$(RABBITMQ_USER)" \
	-e RABBITMQ_PASSWORD="$(RABBITMQ_PASSWORD)" \
	-p "$(RABBITMQ_PORT):$(RABBITMQ_CONTAINER_PORT)" \
	-p "$(RABBITMQ_DEBUG_PORT):$(RABBITMQ_CONTAINER_DEBUG_PORT)" \
	-v $(RABBITMQ_VOLUME):/var/lib/rabbitmq/data \
	--health-cmd="rabbitmq-diagnostics ping" \
	--health-interval=30s \
	--health-timeout=10s \
	--health-retries=5 \
	--network $(DOCKER_NETWORK) \
	docker.io/library/rabbitmq:4.2.1-management-alpine

rabbitmq_stop:
	docker stop $(RABBITMQ_CONTAINER)
	docker rm $(RABBITMQ_CONTAINER)

# Bot image and container
BOT_IMAGE=telegram_download_bot
BOT_CONTAINER=telegram_bot
CONSUMER_CONTAINER_PREFIX=telegram_bot_consumer_

build_bot:
	docker build -t $(BOT_IMAGE):bot -f Dockerfile.bot .

build_consumer:
	docker build -t $(BOT_IMAGE):consumer -f Dockerfile.consumer .

# Run containers
bot_run: docker_net
	docker run -d \
	  --name $(BOT_CONTAINER) \
	  -e POSTGRES_HOST="$(POSTGRES_CONTAINER)" \
	  -e POSTGRES_PORT="$(POSTGRES_CONTAINER_PORT)" \
	  -e POSTGRES_DATABASE="${POSTGRES_DATABASE}" \
	  -e POSTGRES_USER="${POSTGRES_USER}" \
	  -e POSTGRES_PASSWORD="${POSTGRES_PASSWORD}" \
	  -e RABBITMQ_HOST="$(RABBITMQ_CONTAINER)" \
	  -e RABBITMQ_PORT="${RABBITMQ_CONTAINER_PORT}" \
		-e RABBITMQ_DEBUG_PORT="${RABBITMQ_DEBUG_PORT}"\
	  -e RABBITMQ_USER="${RABBITMQ_USER}" \
	  -e RABBITMQ_PASSWORD="${RABBITMQ_PASSWORD}" \
	  -e RABBITMQ_QUEUE_NAME="${RABBITMQ_QUEUE_NAME}" \
	  -e TELEGRAM_TOKEN="$(TELEGRAM_TOKEN)" \
	  --network $(DOCKER_NETWORK) \
	  $(BOT_IMAGE):bot

consumer_run_%: docker_net
	docker run -d \
	  --name $(CONSUMER_CONTAINER_PREFIX)$* \
	  -e POSTGRES_HOST="$(POSTGRES_CONTAINER)" \
	  -e POSTGRES_PORT="$(POSTGRES_CONTAINER_PORT)" \
	  -e POSTGRES_DATABASE="${POSTGRES_DATABASE}" \
	  -e POSTGRES_USER="${POSTGRES_USER}" \
	  -e POSTGRES_PASSWORD="${POSTGRES_PASSWORD}" \
	  -e RABBITMQ_HOST="$(RABBITMQ_CONTAINER)" \
	  -e RABBITMQ_PORT="${RABBITMQ_CONTAINER_PORT}" \
		-e RABBITMQ_DEBUG_PORT="${RABBITMQ_DEBUG_PORT}"\
	  -e RABBITMQ_USER="${RABBITMQ_USER}" \
	  -e RABBITMQ_PASSWORD="${RABBITMQ_PASSWORD}" \
	  -e RABBITMQ_QUEUE_NAME="${RABBITMQ_QUEUE_NAME}" \
	  -e TELEGRAM_TOKEN="$(TELEGRAM_TOKEN)" \
	  -v $(pwd)/videos/consumer_$*:/app/videos \
	  --network $(DOCKER_NETWORK) \
	  $(BOT_IMAGE):consumer

# 3 consumers
consumers_run: consumer_run_1 consumer_run_2 consumer_run_3

# Stop containers 
bot_stop:
	docker stop $(BOT_CONTAINER)
	docker rm $(BOT_CONTAINER)

stop_consumer_%:
	docker stop $(CONSUMER_CONTAINER_PREFIX)$* || true
	docker rm $(CONSUMER_CONTAINER_PREFIX)$* || true

consumers_stop: stop_consumer_1 stop_consumer_2 stop_consumer_3

# Logs
logs_bot:
	docker logs -f $(BOT_CONTAINER)

logs_consumer_%:
	docker logs -f $(CONSUMER_CONTAINER_PREFIX)$*

# Combined
infrastructure_up: postgres_run rabbitmq_run

infrastructure_down: postgres_stop rabbitmq_stop

all_up: infrastructure_up build_bot build_consumer bot_run consumers_run

all_down: bot_stop consumers_stop infrastructure_down


check_consumers_logs:
	docker logs $(CONSUMER_CONTAINER_PREFIX)1 --tail 10
	docker logs $(CONSUMER_CONTAINER_PREFIX)2 --tail 10
	docker logs $(CONSUMER_CONTAINER_PREFIX)3 --tail 10

check_logs:
	docker logs $(POSTGRES_CONTAINER) --tail 30
	docker logs $(RABBITMQ_CONTAINER) --tail 30  
	docker logs $(BOT_CONTAINER) --tail 30
	docker logs $(CONSUMER_CONTAINER_PREFIX)1 --tail 30
	docker logs $(CONSUMER_CONTAINER_PREFIX)2 --tail 30
	docker logs $(CONSUMER_CONTAINER_PREFIX)3 --tail 30

status:
	docker ps -a --filter "name=telegram_bot"

all_down_if_not_all_up:
	docker stop telegram_bot_postgres_database bot_downloader_postgres_data bot_downloader_rabbitmq_data telegram_bot_rabbitmq telegram_bot telegram_bot_consumer_1 telegram_bot_consumer_2 telegram_bot_consumer_3 2>/dev/null || true
	docker rm telegram_bot_postgres_database bot_downloader_postgres_data bot_downloader_rabbitmq_data telegram_bot_rabbitmq telegram_bot telegram_bot_consumer_1 telegram_bot_consumer_2 telegram_bot_consumer_3 2>/dev/null || true
	docker volume rm postgres_data rabbitmq_data 2>/dev/null || true
	docker network rm bot_downloader_network 2>/dev/null || true

refresh: all_down all_down_if_not_all_up all_up

# Alternative - docker-compose

compose_all_up:
	sudo docker-compose up -d --scale consumer=3

compose_all_down:
	docker-compose down

compose_all_logs:
	docker-compose logs -f

compose_all_status:
	docker-compose ps

compose_all_restart:
	docker-compose down
	docker-compose up -d --scale consumer=3

compose_consumers_logs:
	docker-compose logs -f consumer

compose_bot_logs:
	docker-compose logs -f telegram_bot

compose_all_rebuild:
	docker-compose down
	docker-compose build --no-cache
	docker-compose up -d --scale consumer=3
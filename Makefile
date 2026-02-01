init:
	poetry install
	docker compose up -d
	poetry run edgar db init

pack:
	poetry run edgar build-pack --ticker $(TICKER) --peers $(PEERS)

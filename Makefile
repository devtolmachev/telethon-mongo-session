.PHONY: tests

SOURCE_CODE_DIR = telethon-mongo-session

tests:
	@echo "Running tests with pytest"
	@pytest --cov=$(SOURCE_CODE_DIR) --cov-report== telethon-mongo-session

update-coverage:
	@pytest --cov=$(SOURCE_CODE_DIR) --cov-report= telethon-mongo-session
	@genbadge coverage -i coverage.xml -o .github/badges/coverage.svg

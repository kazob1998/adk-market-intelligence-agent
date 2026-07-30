.PHONY: install test eval run docker-build clean

install:
	pip install -r requirements.txt

test:
	PYTHONPATH=. python3 -m unittest discover -s tests -p "test_*.py"

eval:
	PYTHONPATH=. python3 cli.py --query "Analyze GOOGL risk and market performance" --eval

run:
	python3 -m uvicorn src.web.app:app --host 0.0.0.0 --port 8080 --reload

cli:
	python3 cli.py --query "Analyze GOOGL risk and market performance"

docker-build:
	docker build -t adk-market-intelligence-agent:latest .

docker-run:
	docker run -p 8080:8080 adk-market-intelligence-agent:latest

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

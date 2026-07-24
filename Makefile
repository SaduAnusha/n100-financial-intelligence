load:
	python src/etl/loader.py

ratios:
	python src/etl/ratio_engine.py

test:
	pytest tests/ -v --cov=src

report:
	python src/reports/generate_reports.py

dashboard:
	streamlit run src/dashboard/app.py

api:
	python src/api/main.py

clean:
	rmdir /s /q output
	mkdir output
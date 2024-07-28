pip freeze > requirements.txt
fastapi dev main.py --port 8000 --host 0.0.0.0
pip install -r requirements.txt
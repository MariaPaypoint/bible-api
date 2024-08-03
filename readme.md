

pip install -r requirements.txt

source venv/bin/activate
fastapi dev app/main.py --port 8000 --host 0.0.0.0

pip freeze > requirements.txt

brew install openapi-generator
openapi-generator generate -i http://127.0.0.1:8000/openapi.json -g swift-combine -o /Users/maria/Desktop/Dev/BiblePause/LibApi


https://www.doctave.com/blog/python-export-fastapi-openapi-spec
python extract-openapi.py --app-dir app main:app --out openapi_generated.yaml
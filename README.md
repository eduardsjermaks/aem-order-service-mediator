# AEM Order Service Layered

Minimal FastAPI project scaffold with pytest and FastAPI TestClient.

## Setup

Create and activate a virtual environment:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

Install dependencies:

```powershell
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

## Run the app

```powershell
python -m uvicorn app.main:app --reload
```

Then open:

- http://127.0.0.1:8000/health

## Run tests

```powershell
python -m pytest -q
```

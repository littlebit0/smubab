@echo off
cd /d C:\Users\littlebit\.openclaw\workspace\smubab\backend
python -m uvicorn main:app --host 0.0.0.0 --port 8000

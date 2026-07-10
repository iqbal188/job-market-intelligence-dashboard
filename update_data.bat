@echo off

cd /d D:\Project\job-market-intelligence

call venv\Scripts\activate

python run_pipeline.py

pause
FROM python:3.12.12-slim-bookworm
WORKDIR /workspace
COPY services/workspace/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt && useradd -m workspace
COPY services/workspace/app.py .
RUN chmod -R a+rX /workspace
USER workspace
CMD ["streamlit", "run", "app.py", "--server.address=0.0.0.0", "--server.port=8501", "--browser.gatherUsageStats=false"]

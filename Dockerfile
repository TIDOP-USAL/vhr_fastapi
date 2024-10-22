FROM python:3.10
WORKDIR /usr/src/app
RUN apt-get update && apt-get install -y curl
RUN pip install --upgrade pip
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE 8000
# CMD python ./src/server.py
CMD ["gunicorn", "-k", "uvicorn.workers.UvicornWorker", "-w", "4", "src.server:app", "-b", "0.0.0.0:8000"]

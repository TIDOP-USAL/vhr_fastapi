FROM python:3.10
WORKDIR /usr/src/app
RUN apt-get update && apt-get install -y curl
RUN apt-get update && apt-get install ffmpeg libsm6 libxext6  cron -y
RUN pip install --upgrade pip
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
COPY . .

RUN echo "0 */2 * * * rm -rf /usr/src/app/output/tmp*" > /etc/cron.d/cleanup_tmp

RUN chmod 0644 /etc/cron.d/cleanup_tmp
RUN crontab /etc/cron.d/cleanup_tmp
RUN touch /var/log/cron.log

EXPOSE 8000
CMD cron && gunicorn -k uvicorn.workers.UvicornWorker -w 4 -b 0.0.0.0:8000 --chdir ./src server:app

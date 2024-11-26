FROM python:3.10
WORKDIR /usr/src/app

# Instalar dependencias del sistema
RUN apt-get update && apt-get install -y curl ffmpeg libsm6 libxext6 cron supervisor

# Instalar dependencias de Python
RUN pip install --upgrade pip
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
COPY . .

# Configurar Cron para limpiar archivos temporales cada 2 horas
RUN echo "0 */2 * * * rm -rf /usr/src/app/output/tmp*" > /etc/cron.d/cleanup_tmp
RUN chmod 0644 /etc/cron.d/cleanup_tmp
RUN crontab /etc/cron.d/cleanup_tmp

# Configurar supervisord
COPY supervisord.conf /etc/supervisor/conf.d/supervisord.conf

EXPOSE 8000

# Usar supervisord como proceso principal
CMD ["supervisord", "-c", "/etc/supervisor/conf.d/supervisord.conf"]

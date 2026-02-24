#FROM python:3.12-slim
FROM registry2.iran.liara.ir/local/python:3.12-slim

# APT Mirror and disable SSL
RUN sed -i 's/deb.debian.org/mirror-linux.runflare.com/g' /etc/apt/sources.list.d/debian.sources
RUN sed -i 's/security.debian.org/mirror-linux.runflare.com/g' /etc/apt/sources.list.d/debian.sources
RUN sed -i 's/https/http/g' /etc/apt/sources.list.d/debian.sources

ENV PYTHONUNBUFFERED=1 \
    PIP_INDEX_URL=https://mirror-pypi.runflare.com/simple

# Install Linux Dependencies
RUN apt-get update -o Acquire::Check-Valid-Until=false
RUN apt-get install -y --no-install-recommends build-essential libpq-dev curl gnupg nano supervisor nginx tzdata bash libmagic1 -o Acquire::Check-Valid-Until=false
RUN apt-get clean
RUN rm -rf /var/lib/apt/lists/*

# Set TZ
ENV TZ=Asia/Tehran
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime
RUN echo $TZ > /etc/timezone

# Create app directory
WORKDIR /app

# Copy source
COPY . ./

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install --no-cache-dir gunicorn

# Create necessary directories
RUN mkdir -p /var/log/project_title/nginx \
    /var/log/project_title/supervisor \
    /var/log/project_title/django

# System Config Files
COPY supervisord.conf /etc/supervisor/conf.d/supervisord.conf
COPY nginx.conf /etc/nginx/nginx.conf


# Entrypoint
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh
ENTRYPOINT ["/entrypoint.sh"]

# Only expose Nginx port (gateway)
EXPOSE 80
CMD ["supervisord", "-c", "/etc/supervisor/conf.d/supervisord.conf", "-n"]
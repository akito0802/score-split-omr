FROM ubuntu:24.04
ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update && apt-get install -y curl ca-certificates python3 python3-pip libfreetype6 fontconfig && rm -rf /var/lib/apt/lists/*
ARG AUDIVERIS_VERSION=5.11.0
RUN curl -L -o /tmp/audiveris.deb "https://github.com/Audiveris/audiveris/releases/download/${AUDIVERIS_VERSION}/Audiveris-${AUDIVERIS_VERSION}-ubuntu24.04-x86_64.deb" \
 && apt-get update && apt-get install -y /tmp/audiveris.deb \
 && rm -f /tmp/audiveris.deb && rm -rf /var/lib/apt/lists/*
WORKDIR /app
COPY requirements.txt .
RUN pip3 install --break-system-packages --no-cache-dir -r requirements.txt
COPY app.py .
ENV PORT=10000
CMD ["sh","-c","gunicorn -b 0.0.0.0:$PORT --timeout 120 --workers 1 app:app"]

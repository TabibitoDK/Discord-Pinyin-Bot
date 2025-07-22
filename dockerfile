FROM python:3.9

WORKDIR /code

# Install system dependencies and CJK fonts
RUN apt-get update && apt-get install -y \
    fonts-noto-cjk \
    fonts-noto-cjk-extra \
    fonts-dejavu-core \
    fontconfig \
    ffmpeg \
    && fc-cache -fv \
    && rm -rf /var/lib/apt/lists/*

# Configure DNS
RUN echo "nameserver 8.8.8.8" > /etc/resolv.conf && \
    echo "nameserver 8.8.4.4" >> /etc/resolv.conf

COPY requirements.txt /code/requirements.txt

RUN pip install --no-cache-dir --upgrade -r /code/requirements.txt

COPY . /code

EXPOSE 7860

CMD ["python", "-u", "app.py"]
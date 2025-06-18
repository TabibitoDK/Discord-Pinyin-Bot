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

COPY requirements.txt /code/requirements.txt

RUN pip install --no-cache-dir --upgrade -r /code/requirements.txt

COPY . /code

EXPOSE 7860

CMD ["python", "-u", "app.py"]
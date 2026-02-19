# Use lightweight official Python runtime as parent image
FROM python:3.11-slim

# set workdir
WORKDIR /app

# copy requirements first to leverage caching
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# copy rest of the source
COPY . .

# expose nothing (bot uses polling)

# default command
CMD ["python", "signal_bot.py"]

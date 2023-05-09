FROM ubuntu:18.04
ENV LANG C.UTF-8
# Add build base and other requirements
RUN apt-get update && apt-get upgrade -y && apt-get install -y build-essential gcc g++ git libpq-dev make \
    python3-pip libcairo2 libpango-1.0-0 libpangocairo-1.0-0 libgdk-pixbuf2.0-0 libffi-dev shared-mime-info \
    libxml2-dev libxslt-dev libssl-dev uwsgi uwsgi-plugin-python3 python3 python3-dev nano

# Employing the layer caching strategy
COPY requirements.txt /
RUN pip3 install --upgrade pip
RUN pip3 install --upgrade setuptools
RUN pip3 install --no-cache-dir -r /requirements.txt

RUN apt-get remove -y git

# Move the source code into the main folder
COPY . /app

# Change working directory 
WORKDIR /app

CMD [ "gunicorn", "-w 8", "-b 0.0.0.0:8080", "api:app"]
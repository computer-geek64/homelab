# Dockerfile
FROM ubuntu:latest
WORKDIR /code

ENTRYPOINT ["./start.sh"]
CMD ["-d"]

RUN apt-get update --fix-missing
RUN apt-get install -y unbound python3 python3-pip libpq-dev

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY src .
RUN cp unbound.conf /etc/unbound/unbound.conf

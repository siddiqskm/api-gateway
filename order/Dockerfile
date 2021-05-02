FROM python:latest

LABEL   app_name  orders
LABEL   env       production

WORKDIR /app

COPY requirements.txt requirements.txt
RUN pip3 install -r requirements.txt

COPY . .

ENV PORT 5000

ENTRYPOINT ["python"]

CMD ["app.py"]

FROM python:alpine3.19

WORKDIR /app

COPY . /app

RUN pip install flask

CMD ["python3", "api-calculator.py"]

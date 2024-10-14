FROM python:alpine3.19

WORKDIR /calculator

COPY . /calculator

RUN pip install flask

CMD ["python3", "api-calculator.py"]

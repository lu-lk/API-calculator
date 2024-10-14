# API-calculator

Для начала нужно написать API-калькулятор. Для этого будет использоваться python, так как на нем это сделать проще. Выберем библиотеку Flask, которая применяется для создания веб-приложений. Калькулятор обладает минимальным необходимым функционалом.  
Напишем Dockerfile, чтобы запустить калькулятор в контейнере docker. 
```  
FROM python:alpine3.19

WORKDIR /app

COPY . /app

RUN pip install flask

CMD ["python3", "api-calculator.py"]
```  
![image](https://github.com/user-attachments/assets/502ffc6b-f0b0-458b-96eb-a36f1085d44a)

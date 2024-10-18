# API-calculator

## Написание API-калькулятора и Dockerfile
Работа будет выполняться на Ubuntu 22.04   
Для начала нужно написать API-калькулятор. Для этого будет использоваться python, так как на нем это сделать проще. Выберем библиотеку Flask, которая применяется для создания веб-приложений. Калькулятор обладает необходимым функционалом.  
  
Напишем Dockerfile, чтобы запустить калькулятор в контейнере docker.   
```
# Назначаем базовый образ  
FROM python:alpine3.19

# Рабочая директория, где будут выполняться дальнейшие инструкции  
WORKDIR /calculator

# Копирование калькулятора в рабочую директорию  
COPY . /calculator

# Установка Flask для работы калькулятора  
RUN pip install flask

# Запуск самого калькулятора  
CMD ["python3", "api-calculator.py"]
```
В качестве базового образа для нашего образа был выбран python, который установлен на alpine. Он весит меньше по сравнению с дебианом и не содержит уязвимостей (Скрин с dockerhub)
![image](https://github.com/user-attachments/assets/80950483-ae75-4827-beb5-ccae3784a78f)  
  
Размещаем файл калькулятора и Dockerfile в одной директории и собираем образ из этой директории:  
![image](https://github.com/user-attachments/assets/6bf622d7-c0b0-4a5e-81e7-7f8486de2944)  

Запускаем контейнер на порту 5555 и проверим, что он запустился:  
![image](https://github.com/user-attachments/assets/c5682304-187d-4ab3-92cd-f02a7ac50b2f)
  
Чтобы проверить функциональность и доступность контейнера отправим ему запросы через curl. Видим, что вернулись ответы:  
![image](https://github.com/user-attachments/assets/7b348a80-449e-48cf-b452-54300dbe1dad)

## Создание пайплайна для обновления версии калькулятора и встраивание инструментов безопасности  

В качестве платформы для сборки, сканирования и тестирования был выбран Gitlab CI/CD.  
  
Установка проводится локально с помощью docker-compose, его инструкции позволяют запускать несколько контейнеров. Файл docker-compose.yml был взят с https://docs.gitlab.com/ee/install/docker/installation.html    
```  
version: '3.6'
services:
  gitlab:
    # Укажем последнюю версию gitlab community edition
    image: gitlab/gitlab-ce:17.4.2-ce.0
    container_name: gitlab
    restart: always
    hostname: 'gitlab.for.calculator'
    environment:
      GITLAB_OMNIBUS_CONFIG: |
        # url для доступа к гитлабу
        external_url 'https://gitlab.for.calculator'
    ports:
      - '80:80'
      - '443:443'
      - '22:22'
    volumes:
      - '$GITLAB_HOME/config:/etc/gitlab'
      - '$GITLAB_HOME/logs:/var/log/gitlab'
      - '$GITLAB_HOME/data:/var/opt/gitlab'
    shm_size: '256m'
    networks:
      - gitlab_net

networks:
  gitlab_net:
    driver: bridge
```
Сеть нужно указать, чтобы в дальнейшем поместить в нее Gitlab и Gitlab-runner.  
Перед запуском нужно поместить переменную для пути gitlab: *export GITLAB_HOME=/srv/gitlab*  
  
Запускаем контейнер:  
![image](https://github.com/user-attachments/assets/ebea6c9e-b49d-4858-8b40-2fa9e701978b)  

Чтобы авторизоваться в gitlab, нужно знать пароль от root. Заходим в контейнер c gitlab и достаем пароль из файла:  
![image](https://github.com/user-attachments/assets/b45c206e-08dd-4c90-ba5b-aa289110fc61)  

Следует подключиться к Gitlab через Web-интерфейс. Узнаем адрес машины, где развернут gitlab и зайдем на него по https через браузер. Авторизуемся и создаем проект.

```
version: '3.6'
services:
  gitlab:
    image: gitlab/gitlab-ce:17.4.2-ce.0
    container_name: gitlab
    restart: always
    hostname: 'gitlab.for.calculator'
    environment:
      GITLAB_OMNIBUS_CONFIG: |
        external_url 'https://gitlab.for.calculator'
    ports:
      - '80:80'
      - '443:443'
      - '22:22'
    volumes:
      - '/srv/gitlab/config:/etc/gitlab'
      - '/srv/gitlab/logs:/var/log/gitlab'
      - '/srv/gitlab/data:/var/opt/gitlab'
    shm_size: '256m'
    networks:
      - gitlab_net

  gitlab-runner:
    image: gitlab/gitlab-runner:alpine
    container_name: gitlab-runner
    restart: unless-stopped
    depends_on:
      - gitlab
    volumes:
      - '$GITLAB_RUNNER_HOME:/etc/gitlab-runner'
      - /var/run/docker.sock:/var/run/docker.sock
    networks:
      - gitlab_net

networks:
  gitlab_net:
    driver: bridge
```
*export GITLAB_RUNNER_HOME=/srv/gitlab-runner*  
![image](https://github.com/user-attachments/assets/eef70594-6998-473e-9b3b-fbab3599bdae)  
![image](https://github.com/user-attachments/assets/0a627fea-ae5f-45e0-bdb0-04088a10d61c)


  
![image](https://github.com/user-attachments/assets/2d0e75a9-4017-440a-8754-7ee81064719a)

В файле конфигурации раннера config.toml выставляем privileged = true; добавляем /var/run/docker.sock:/var/run/docker.sock в volume. Это нужно для работы Docker-in-Docker.

![image](https://github.com/user-attachments/assets/d165bc12-9510-4c66-b704-549db5cd63ce)





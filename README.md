# API-calculator

## Написание API-калькулятора и Dockerfile
 
Для начала нужно написать API-калькулятор. Для этого будет использоваться python. Выберем библиотеку Flask, которая применяется для создания веб-приложений. Калькулятор обладает необходимым функционалом.  
  
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

**Установка и настройка Gitlab**  
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
      - '/srv/gitlab/config:/etc/gitlab'
      - '/srv/gitlab/logs:/var/log/gitlab'
      - '/srv/gitlab/data:/var/opt/gitlab'
    shm_size: '256m'
    networks:
      - gitlab_net

networks:
  gitlab_net:
    driver: bridge
```
Сеть нужно указать, чтобы в дальнейшем поместить в нее Gitlab и Gitlab-runner.  
  
Запускаем контейнер:  
![image](https://github.com/user-attachments/assets/ebea6c9e-b49d-4858-8b40-2fa9e701978b)  

Чтобы авторизоваться в gitlab, нужно знать пароль от root. Заходим в контейнер c gitlab и достаем пароль из файла:  
![image](https://github.com/user-attachments/assets/b45c206e-08dd-4c90-ba5b-aa289110fc61)  

Следует подключиться к Gitlab через Web-интерфейс. Узнаем адрес машины, где развернут gitlab и зайдем на него по https через браузер. Авторизуемся и создаем проект. 
Для выполнения задач пайплайна будет нужен gitlab-runner - добавим конфигурацию для его запуска в docker-compose.yml:

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
      - '/srv/gitlab-runner:/etc/gitlab-runner'
      - /var/run/docker.sock:/var/run/docker.sock
    networks:
      - gitlab_net

networks:
  gitlab_net:
    driver: bridge
```
  
Запустим docker compose и проверим контейнеры:  
![image](https://github.com/user-attachments/assets/eef70594-6998-473e-9b3b-fbab3599bdae)  

Получаем токен Gitlab-runner через интерфейс Gitlab. Заходим в контейнер с Gitlab-runner и регистрируем его для взаимодействия с Gitlab:   
![image](https://github.com/user-attachments/assets/2d0e75a9-4017-440a-8754-7ee81064719a)  
В файле конфигурации раннера config.toml выставляем privileged = true; добавляем /var/run/docker.sock:/var/run/docker.sock в volume. Это нужно для работы Docker-in-Docker.  

**Установка и настройка Harbor регистри**  

Для работы с образами локально был развернут регистри Harbor. Его конфиг:  
![image](https://github.com/user-attachments/assets/d165bc12-9510-4c66-b704-549db5cd63ce)

Авторизуемся и создаем проект, где в дальнейшем будут храниться образы:  
![image](https://github.com/user-attachments/assets/13a2c91f-be32-4f50-8995-3eb1cc75f91f)  

**Пайплайн .gitlab-ci.yml**  
```  
stages:
  - semgrep
  - build
  - trivy
  - deploy

scan_with_semgrep:
  stage: semgrep
  image: returntocorp/semgrep:latest
  script:
    # Статическое сканирование директории проекта
    - semgrep --config auto --json --output scanning-with-semgrep.json $CI_PROJECT_DIR
    # Сборка останавливается если обнаружена CRITICAL уязвимость
    - |
      if grep -q '"confidence": "CRITICAL"' scanning-with-semgrep.json; then
        echo "CRITICAL уязвимости найдены!"
        exit 1
      else
        echo "CRITICAL уязвимости не обнаружены."
      fi
  artifacts:
   paths:
      - scanning-with-semgrep.json # Сохранение отчета в артефакты для дальнейшего анализа

build_calculator:
  stage: build
  image: docker:latest
  services:
    - name: docker:dind # Docker-in-Docker для сборки и управления образом
  script:
    - docker build -t $HARBOR_URL/$IMAGE_NAME_TAG . # Сборка образа пуша в регистри
    - docker login $HARBOR_URL -u $HARBOR_LOGIN -p $HARBOR_PASSWORD # Авторизация в Harbor регистри
    - docker push $HARBOR_URL/$IMAGE_NAME_TAG # Пуш образа

scan_with_trivy:
  stage: trivy
  image: 
    name: aquasec/trivy:latest
    entrypoint: [""]
  script:
    # Сканирование инфраструктуры образа через trivy. Если будет найдена CRITICAL уязвимость, то пайплайн остановится
    - trivy image --exit-code 1 --severity CRITICAL --format json --output scanning-with-trivy.json $HARBOR_URL/$IMAGE_NAME_TAG
  artifacts:
    paths:
      - scanning-with-trivy.json

deploy_container:
  stage: deploy
  image: docker:latest
  services:
    - name: $HARBOR_URL/$IMAGE_NAME_TAG
      alias: api-calculator # alias для указания доменного имени в сети
  before_script:
    - apk add --no-cache curl
  script:
    - curl "http://api-calculator:5555/multiply?a=10.2313&b=0.22" # Отправка запросов для проверки работы калькулятора
    - curl "http://api-calculator:5555/"
    - curl "http://api-calculator:5555/divide?a=999&b=0"
```  
Пайплайн состоит из 4 джоб:  
Первая джоба сканирует код с помощью статического анализатора кода semgrep. Если будет найдена critical уязвимость, то пайплайн останавливается. Отчет сканирования сохраняется в артефакты.  
Результат:  
![image](https://github.com/user-attachments/assets/56ac602d-a4f4-4b02-ada7-5200b8591ca4)  
  
Вторая джоба собирает контейнер с помощью d-in-d и пушит его в локальный регистри.  
Образ в регистри:  
![image](https://github.com/user-attachments/assets/240b750b-08a7-47c9-9983-55b4d29cc4bf)  
  
Третья джоба сканирует образ калькулятора с помощью trivy. Если будет найдена critical уязвимость, то пайплайн также останавливается. Отчет сканирования сохраняется в артефакты.  
  
Последняя джоба отвечает за запуск контейнера с калькулятором и за отправку запросов для проверки его работоспособности.
![image](https://github.com/user-attachments/assets/2cc452f0-063d-42ee-b934-3e0ae4483648)  

Переменные хранятся в Settings -> CI/CD -> Variables:  
![image](https://github.com/user-attachments/assets/06ffa5be-f01e-404d-b05c-9420bda18906)  

## Анализ отчетов сканирования








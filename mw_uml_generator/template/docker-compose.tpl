version: '2'
services:
  {{ project }}:
    build: .
    image: {{ project }}
    container_name: {{ project }}_py35
    restart: always
    environment:
      LOG_LEVEL: ${LOG_LEVEL}
      CONSUL_HTTP_ADDR: ${CONSUL_HTTP_ADDR}
      {% for k in envs.keys() %}
      {{ k }}: ${{ '{'+k+'}' }}
      {% endfor %}
    ports:
      - ${WEB_PORT}:${WEB_PORT}
    volumes:
      - /usr/share/zoneinfo/Asia/Taipei:/usr/share/zoneinfo/Asia/Taipei
      - /usr/share/zoneinfo/Asia/Taipei:/etc/localtime/
      - /etc/timezone:/etc/timezone
      - .:/var/{{ project }}
    working_dir: /var/{{ project }}
    command: ["python3","run.py"]
    logging:
      driver: "json-file"
      options:
        max-size: "50m"
        max-file: "10"

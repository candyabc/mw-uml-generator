#!/usr/bin/env bash
# consul的host 格式 ip:port
export CONSUL_HTTP_ADDR="192.168.101.172:8500"
# web的port
export WEB_PORT=8080

## log的級別，10：debug，20：info，30：warn，40：error，50：critical，log會影響程序性能
export LOG_LEVEL=10

{% for k,v in envs.items() %}
export{{ k }}  = {{ v }}
{% endfor %}
docker-compose up -d

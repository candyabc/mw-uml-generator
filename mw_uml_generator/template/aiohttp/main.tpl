from aiohttp_swagger import setup_swagger
from aiohttp import web
from .apis import ({% for swagger in swaggers %}{{ swagger.model_routename() }},{% endfor %})
from .config import configs
import os
import asyncio
import yaml
import logging



try:
    # 只有Linux下才能运行
    import uvloop
    asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())
except Exception as e:
    pass

async def after_start_app(app):
    app.logger.info("on start app")
    # app['db']=

    #todo :here is for app start

async def on_cleanup(app):
    app.logger.info('on clean up')
    # todo :here is for app clean up ,eg: db.close etc.

def init_app(app):
    #todo:
    app['config'] = configs.get(app['mode'])()
    logging.basicConfig(app['config'].log_level,format = '%(asctime)s %(name)-12s %(levelname)-8s %(message)s')





def setup_swagger_file(app,swagger_name,swagger_url):
    _filename =os.path.join(os.path.dirname(__file__),'swagger/%s.yml' % swagger_name)
    with open(_filename) as f:
        swaggerinfo =yaml.load(f.read())
        swaggerinfo['host']='%s:%s' % (app['config'].myaddress, app['config'].port)
    setup_swagger(app,
                  swagger_info=swaggerinfo
                  ,swagger_url=swagger_url)  # <-- Loaded Swagger from external YAML file


def create_app():
    app = web.Application(debug=False )
    app['mode']=os.environ.get('mode','default')
    init_app(app)
    app.on_startup.append(after_start_app)
    app.on_cleanup.append(on_cleanup)
    app.logger.setLevel(app['config'].log_level)
    # set up swagger file
    {% for swagger in swaggers %}
    setup_swagger_file(app,'{{ swagger.name }}',{{ swagger.model_routename()}}.gen_full_url('/doc'))
    {{ swagger.model_routename()}}.config_routes(app)
    {% endfor %}

    return app

def main():
    app = create_app()
    web.run_app(app,port=app['config'].port)

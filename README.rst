================
mw-uml-generator
================

根据uml的类图来产生dbmodel和swagger的工具，


Description
===========

根据uml的类图来产生dbmodel和swagger的工具，产生flask 或 aiohttp 的工程(python)

Note
====

安装
====
::

    git 下载

    python setup.py build sdist
    python install

使用
====
::

    gencode -h 查看使用方法
    1. gencode create [project_name]  来产生配置工程及文件
        产生工程目录，及配置文件，uml文件

    2. cd project_name
       修改 uml文件

    3. gencode up [-o --overwrite]
        根据uml文件产生工程代码


    4. 产生docker-compose file
       在gencodeFile的env中设定环境变量
       gencode docker [-o --overwrite]

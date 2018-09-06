from aiohttp import web
{% for op in operations %}
async def {{ op.operatorid }}(request):
    pass
{% endfor %}
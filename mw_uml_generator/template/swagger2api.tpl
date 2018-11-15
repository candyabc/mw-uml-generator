import base from './base'
const qs = require('qs');
function baseuri() {
  return `${base.baseurl}{{ basePath }}`
}
const PER_PAGE = 20
{% for route in routes %}
export async function {{ route.func }}({% if route.query_as_args %}{{ route.query_as_args }},{% endif %}data,headers={}) {
  let url =`${baseuri()}{{ route.path_as_url }}`
  {% if route.query_as_url %}
  let _qs =  {{ route.query_as_url  }}
  let query_str =qs.stringify(_qs, { skipNulls: true })
  if (query_str!='') {
      url +='?'+query_str
  }
  {% endif %}
  {% if route.header_as_str %}
  headers = Object.assign(headers ,{{ route.header_as_str }})
  {% endif %}
  {% if route.header_params|length>0 %}
  {% for param in route.header_params %}
  headers = Object.assign(headers,{ {{ param.name }}:{{ param.name }} }
  {% endfor %}
  {% endif %}
  return await base.{{ route.method }}(url,data,headers)
}

{% endfor %}

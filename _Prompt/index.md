---
layout: default
title: Prompts
permalink: /prompts/
---
<ul>
{% for item in site.prompts %}
  <li><a href="{{ item.url }}">{{ item.title }}</a></li>
{% endfor %}
</ul>
#!/usr/bin/python
# -*- coding: UTF-8 -*-
import sae
import code

application = sae.create_wsgi_app(code.app.wsgifunc())

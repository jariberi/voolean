# -*- coding: utf8 -*-
import logging
from suds.client import Client
import sys
__author__ = "Jorge Riberi <jariberi@gmail.com>"

logger = logging.getLogger("voolean")

class WebServiceAFIP:
    "Infraestructura basica para interfaces webservices de AFIP"

    def __init__(self, produccion=False):
        self.produccion = produccion
        self.xml = self.client = None
        self.Token = self.Sign = self.ExpirationTime = None
        self.excMsg = self.excCode = None

    def Conectar(self, wsdl=None, proxy="", wrapper=None, cacert=None, timeout=30, soap_server=None):
        logger.info("Conectando... " + wsdl)
        self.client = Client(url=wsdl)
        return True

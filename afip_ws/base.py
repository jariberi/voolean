# -*- coding: utf8 -*-
from afip_ws.soap import SoapClient

__author__ = "Jorge Riberi <jariberi@gmail.com>"

import functools
import socket
import sys
import os
import stat
import traceback
import warnings
from cStringIO import StringIO
from urllib import urlencode
import mimetools, mimetypes
from Cookie import SimpleCookie

from pysimplesoap.client import SimpleXMLElement, SoapFault, parse_proxy, set_http_wrapper

try:
    import json
except ImportError:
    try:
        import simplejson as json
    except:
        print "para soporte de JSON debe instalar simplejson"
        json = None

try:
    import httplib2
    # corregir temas de negociacion de SSL en algunas versiones de ubuntu:
    import platform

    dist, ver, nick = platform.linux_distribution() if sys.version > (2, 6) else ("", "", "")
    from pysimplesoap.client import SoapClient

    monkey_patch = httplib2._ssl_wrap_socket.__module__ != "httplib2"
    if dist == 'Ubuntu' and ver == '14.04' and not monkey_patch:
        import ssl


        def _ssl_wrap_socket(sock, key_file, cert_file,
                             disable_validation, ca_certs):
            if disable_validation:
                cert_reqs = ssl.CERT_NONE
            else:
                cert_reqs = ssl.CERT_REQUIRED
            return ssl.wrap_socket(sock, keyfile=key_file, certfile=cert_file,
                                   cert_reqs=cert_reqs, ca_certs=ca_certs,
                                   ssl_version=ssl.PROTOCOL_SSLv3)


        httplib2._ssl_wrap_socket = _ssl_wrap_socket

except:
    print "para soporte de WebClient debe instalar httplib2"

DEBUG = False


# Funciones para manejo de errores:


def exception_info(current_filename=None, index=-1):
    "Analizar el traceback y armar un dict con la info amigable user-friendly"
    # guardo el traceback original (por si hay una excepción):
    info = sys.exc_info()  # exc_type, exc_value, exc_traceback
    # importante: no usar unpacking porque puede causar memory leak
    if not current_filename:
        # genero un call stack para ver quien me llamó y limitar la traza:
        # advertencia: esto es necesario ya que en py2exe no tengo __file__
        try:
            raise ZeroDivisionError
        except ZeroDivisionError:
            f = sys.exc_info()[2].tb_frame.f_back
        current_filename = os.path.normpath(os.path.abspath(f.f_code.co_filename))

    # extraer la última traza del archivo solicitado:
    # (útil para no alargar demasiado la traza con lineas de las librerías)
    ret = {'filename': "", 'lineno': 0, 'function_name': "", 'code': ""}
    try:
        for (filename, lineno, fn, text) in traceback.extract_tb(info[2]):
            if os.path.normpath(os.path.abspath(filename)) == current_filename:
                ret = {'filename': filename, 'lineno': lineno,
                       'function_name': fn, 'code': text}
    except Exception, e:
        pass
    # obtengo el mensaje de excepcion tal cual lo formatea python:
    # (para evitar errores de encoding)
    try:
        ret['msg'] = traceback.format_exception_only(*info[0:2])[0]
    except:
        ret['msg'] = '<no disponible>'
    # obtener el nombre de la excepcion (ej. "NameError")
    try:
        ret['name'] = info[0].__name__
    except:
        ret['name'] = 'Exception'
    # obtener la traza formateada como string:
    try:
        tb = traceback.format_exception(*info)
        ret['tb'] = ''.join(tb)
    except:
        ret['tb'] = ""
    return ret


def inicializar_y_capturar_excepciones(func):
    "Decorador para inicializar y capturar errores (version para webservices)"

    @functools.wraps(func)
    def capturar_errores_wrapper(self, *args, **kwargs):
        try:
            # inicializo (limpio variables)
            self.errores = []  # listas de dict para usar en python
            self.observaciones = []
            self.Eventos = []
            self.Traceback = self.Excepcion = ""
            self.ErrCode = self.ErrMsg = self.Obs = ""
            # limpio variables especificas del webservice:
            self.inicializar()
            # actualizo los parámetros
            kwargs.update(self.params_in)
            # limpio los parámetros
            self.params_in = {}
            self.params_out = {}
            # llamo a la función (con reintentos)
            retry = self.reintentos + 1
            while retry:
                try:
                    retry -= 1
                    return func(self, *args, **kwargs)
                except socket.error, e:
                    if e[0] not in (10054, 10053):
                        # solo reintentar si el error es de conexión
                        # (10054, 'Connection reset by peer')
                        # (10053, 'Software caused connection abort')
                        raise
                    else:
                        if DEBUG: print e, "Reintentando..."
                        self.log(exception_info().get("msg", ""))

        except SoapFault, e:
            # guardo destalle de la excepción SOAP
            self.ErrCode = unicode(e.faultcode)
            self.ErrMsg = unicode(e.faultstring)
            self.Excepcion = u"%s: %s" % (e.faultcode, e.faultstring,)
            if self.LanzarExcepciones:
                raise
        except Exception, e:
            ex = exception_info()
            self.Traceback = ex.get("tb", "")
            try:
                self.Excepcion = ex.get("msg", "")
            except:
                self.Excepcion = u"<no disponible>"
            if self.LanzarExcepciones:
                raise
            else:
                self.ErrMsg = self.Excepcion
        finally:
            # guardo datos de depuración
            if self.client:
                self.XmlRequest = self.client.xml_request
                self.XmlResponse = self.client.xml_response

    return capturar_errores_wrapper


class WebServiceAFIP:
    "Infraestructura basica para interfaces webservices de AFIP"

    def __init__(self, reintentos=1):
        self.reintentos = reintentos
        self.xml = self.client = self.Log = None
        self.params_in = {}
        self.inicializar()
        self.Token = self.Sign = ""
        self.LanzarExcepciones = False

    def inicializar(self):
        self.Excepcion = self.Traceback = ""
        self.XmlRequest = self.XmlResponse = ""

    def Conectar(self, wsdl=None, proxy="", wrapper=None, cacert=None, timeout=30, soap_server=None):
        "Conectar cliente soap del web service"
        try:
            # analizar transporte y servidor proxy:
            if wrapper:
                Http = set_http_wrapper(wrapper)
                self.Version = self.Version + " " + Http._wrapper_version
            if isinstance(proxy, dict):
                proxy_dict = proxy
            else:
                proxy_dict = parse_proxy(proxy)
                self.log("Proxy Dict: %s" % str(proxy_dict))
            # deshabilitar verificación cert. servidor si es nulo falso vacio
            if not cacert:
                cacert = None
            elif cacert is True:
                # usar certificados predeterminados que vienen en la biblioteca
                cacert = os.path.join(httplib2.__path__[0], 'cacerts.txt')
            elif cacert.startswith("-----BEGIN CERTIFICATE-----"):
                pass
            else:
                if not os.path.exists(cacert):
                    self.log("Buscando CACERT en conf...")
                    cacert = os.path.join(self.InstallDir, "conf", os.path.basename(cacert))
                if cacert and not os.path.exists(cacert):
                    self.log("No se encuentra CACERT: %s" % str(cacert))
                    warnings.warn("No se encuentra CACERT: %s" % str(cacert))
                    cacert = None  # wrong version, certificates not found...
                    raise RuntimeError("Error de configuracion CACERT ver DebugLog")
                    return False
            # analizar espacio de nombres (axis vs .net):
            # ns = 'ser' if self.WSDL[-5:] == "?wsdl" else None
            self.client = SoapClient(
                wsdl=wsdl,
                proxy=proxy_dict,
                cacert=cacert,
                timeout=timeout,
                ns=None, soap_server=soap_server,
                trace="--trace" in sys.argv)
            self.wsdl = wsdl  # utilizado por TrazaMed (para corregir el location)
            # corrijo ubicación del servidor (puerto http 80 en el WSDL AFIP)
            for service in self.client.services.values():
                for port in service['ports'].values():
                    location = port['location']
                    if location and location.startswith("http://"):
                        warnings.warn("Corrigiendo WSDL ... %s" % location)
                        location = location.replace("http://", "https://").replace(":80", ":443")
                        port['location'] = location
            return True
        except:
            ex = traceback.format_exception(sys.exc_type, sys.exc_value, sys.exc_traceback)
            self.Traceback = ''.join(ex)
            try:
                self.Excepcion = traceback.format_exception_only(sys.exc_type, sys.exc_value)[0]
            except:
                self.Excepcion = u"<no disponible>"
            if self.LanzarExcepciones:
                raise
            return False

    def log(self, msg):
        "Dejar mensaje en bitacora de depuración (método interno)"
        if not isinstance(msg, unicode):
            msg = unicode(msg, 'utf8', 'ignore')
        if not self.Log:
            self.Log = StringIO()
        self.Log.write(msg)
        self.Log.write('\n\r')
        if DEBUG:
            warnings.warn(msg)

    def DebugLog(self):
        "Devolver y limpiar la bitácora de depuración"
        if self.Log:
            msg = self.Log.getvalue()
            # limpiar log
            self.Log.close()
            self.Log = None
        else:
            msg = u''
        return msg

    @property
    def xml_request(self):
        return self.XmlRequest

    @property
    def xml_response(self):
        return self.XmlResponse

    def AnalizarXml(self, xml=""):
        "Analiza un mensaje XML (por defecto el ticket de acceso)"
        try:
            if not xml or xml == 'XmlResponse':
                xml = self.XmlResponse
            elif xml == 'XmlRequest':
                xml = self.XmlRequest
            self.xml = SimpleXMLElement(xml)
            return True
        except Exception, e:
            self.Excepcion = traceback.format_exception_only(sys.exc_type, sys.exc_value)[0]
            return False

    def ObtenerTagXml(self, *tags):
        "Busca en el Xml analizado y devuelve el tag solicitado"
        # convierto el xml a un objeto
        try:
            if self.xml:
                xml = self.xml
                # por cada tag, lo busco segun su nombre o posición
                for tag in tags:
                    xml = xml(tag)  # atajo a getitem y getattr
                # vuelvo a convertir a string el objeto xml encontrado
                return str(xml)
        except Exception, e:
            self.Excepcion = traceback.format_exception_only(sys.exc_type, sys.exc_value)[0]


    def LeerError(self):
        "Recorro los errores devueltos y devuelvo el primero si existe"

        if self.Errores:
            # extraigo el primer item
            er = self.Errores.pop(0)
            return er
        else:
            return ""


class WebClient:
    "Minimal webservice client to do POST request with multipart encoded FORM data"

    def __init__(self, location, enctype="multipart/form-data", trace=False,
                 cacert=None, timeout=30):
        kwargs = {}
        if httplib2.__version__ >= '0.3.0':
            kwargs['timeout'] = timeout
        if httplib2.__version__ >= '0.7.0':
            kwargs['disable_ssl_certificate_validation'] = cacert is None
            kwargs['ca_certs'] = cacert
        self.http = httplib2.Http(**kwargs)
        self.trace = trace
        self.location = location
        self.enctype = enctype
        self.cookies = None
        self.method = "POST"
        self.referer = None

    def multipart_encode(self, vars):
        "Enconde form data (vars dict)"
        boundary = mimetools.choose_boundary()
        buf = StringIO()
        for key, value in vars.items():
            if not isinstance(value, file):
                buf.write('--%s\r\n' % boundary)
                buf.write('Content-Disposition: form-data; name="%s"' % key)
                buf.write('\r\n\r\n' + value + '\r\n')
            else:
                fd = value
                file_size = os.fstat(fd.fileno())[stat.ST_SIZE]
                filename = os.path.basename(fd.name)
                contenttype = mimetypes.guess_type(filename)[0] or 'application/octet-stream'
                buf.write('--%s\r\n' % boundary)
                buf.write('Content-Disposition: form-data; name="%s"; filename="%s"\r\n' % (key, filename))
                buf.write('Content-Type: %s\r\n' % contenttype)
                # buffer += 'Content-Length: %s\r\n' % file_size
                fd.seek(0)
                buf.write('\r\n' + fd.read() + '\r\n')
        buf.write('--' + boundary + '--\r\n\r\n')
        buf = buf.getvalue()
        return boundary, buf

    def __call__(self, *args, **vars):
        "Perform a GET/POST request and return the response"

        location = self.location
        if isinstance(location, unicode):
            location = location.encode("utf8")
        # extend the base URI with additional components
        if args:
            location += "/".join(args)
        if self.method == "GET":
            location += "?%s" % urlencode(vars)

        # prepare the request content suitable to be sent to the server:
        if self.enctype == "multipart/form-data":
            boundary, body = self.multipart_encode(vars)
            content_type = '%s; boundary=%s' % (self.enctype, boundary)
        elif self.enctype == "application/x-www-form-urlencoded":
            body = urlencode(vars)
            content_type = self.enctype
        else:
            body = None

        # add headers according method, cookies, etc.:
        headers = {}
        if self.method == "POST":
            headers.update({
                'Content-type': content_type,
                'Content-length': str(len(body)),
            })
        if self.cookies:
            headers['Cookie'] = self.cookies.output(attrs=(), header="", sep=";")
        if self.referer:
            headers['Referer'] = self.referer

        if self.trace:
            print "-" * 80
            print "%s %s" % (self.method, location)
            print '\n'.join(["%s: %s" % (k, v) for k, v in headers.items()])
            print "\n%s" % body

        # send the request to the server and store the result:
        response, content = self.http.request(
            location, self.method, body=body, headers=headers)
        self.response = response
        self.content = content

        if self.trace:
            print
            print '\n'.join(["%s: %s" % (k, v) for k, v in response.items()])
            print content
            print "=" * 80

        # Parse and store the cookies (if any)
        if "set-cookie" in self.response:
            if not self.cookies:
                self.cookies = SimpleCookie()
            self.cookies.load(self.response["set-cookie"])

        return content

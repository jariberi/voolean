# -*- coding: utf-8 -*-

"Módulo para obtener un ticket de autorización del web service WSAA de AFIP"

# Basado en wsaa.py de Mariano Reingart
import logging
import random
import datetime
from datetime import timedelta
from django.utils.timezone import now
import xml.etree.ElementTree as et
from suds import WebFault
from afip_ws.models import AFIP_Datos_Autenticacion
from voolean.settings import CERT_FILE_TEST, PRIVATE_KEY_FILE, CERT_FILE_PROD
import email, os, sys, warnings
from base import WebServiceAFIP

logger = logging.getLogger("voolean")

__author__ = "Jorge Riberi (jariberi@gmail.com)"

try:
    from M2Crypto import BIO, Rand, SMIME, SSL
except ImportError:
    warnings.warn("No es posible importar M2Crypto (OpenSSL)")
    BIO = Rand = SMIME = SSL = None
    # utilizar alternativa (ejecutar proceso por separado)
    from subprocess import Popen, PIPE
    from base64 import b64encode

SERVICE = "wsfe"  # El nombre del web service al que se le pide el TA

WSAAURL_PROD = "https://wsaa.afip.gov.ar/ws/services/LoginCms?wsdl"  # PRODUCCION!!!
WSAAURL_TEST = "https://wsaahomo.afip.gov.ar/ws/services/LoginCms?wsdl"  # homologacion (pruebas)

# No debería ser necesario modificar nada despues de esta linea

def create_tra(service=SERVICE, ttl=2400):
    "Crear un Ticket de Requerimiento de Acceso (TRA)"
    tra = et.fromstring('<?xml version="1.0" encoding="UTF-8"?>'
                        '<loginTicketRequest version="1.0">'
                        '</loginTicketRequest>')
    # tra = SimpleXMLElement(
    #     '<?xml version="1.0" encoding="UTF-8"?>'
    #     '<loginTicketRequest version="1.0">'
    #     '</loginTicketRequest>')
    header = et.SubElement(tra, 'header')
    # El source es opcional. Si falta, toma la firma (recomendado).
    # tra.header.addChild('source','subject=...')
    # tra.header.addChild('destination','cn=wsaahomo,o=afip,c=ar,serialNumber=CUIT 33693450239')
    et.SubElement(header, 'uniqueId').text = str(random.randint(0, 999999))
    # header.add_child('uniqueId', str(long((time.time()*1000))))
    et.SubElement(header, 'generationTime').text = (datetime.datetime.now() - timedelta(seconds=120)).strftime("%Y-%m-%dT%H:%M:%S")
    # tra.header.add_child('generationTime', str(date('c', date('U') - ttl)))
    et.SubElement(header, 'expirationTime').text = (datetime.datetime.now() + timedelta(seconds=ttl)).strftime(
        "%Y-%m-%dT%H:%M:%S")
    # tra.header.add_child('expirationTime', str(date('c', date('U') + ttl)))
    et.SubElement(tra, 'service').text = service
    # tra.add_child('service', service)
    return '<?xml version="1.0" encoding="UTF-8"?>' + et.tostring(tra)


def sign_tra(tra, cert=None, privatekey=None, passphrase=""):
    "Firmar PKCS#7 el TRA y devolver CMS (recortando los headers SMIME)"

    if BIO:
        # Firmar el texto (tra) usando m2crypto (openssl bindings para python)
        buf = BIO.MemoryBuffer(tra)  # Crear un buffer desde el texto
        # Rand.load_file('randpool.dat', -1)     # Alimentar el PRNG
        s = SMIME.SMIME()  # Instanciar un SMIME
        # soporte de contraseña de encriptación (clave privada, opcional)
        callback = lambda *args, **kwarg: passphrase
        # Cargar clave privada y certificado
        if not privatekey.startswith("-----BEGIN RSA PRIVATE KEY-----"):
            # leer contenido desde archivo (evitar problemas Applink / MSVCRT)
            if os.path.exists(privatekey) and os.path.exists(cert):
                privatekey = open(privatekey).read()
                cert = open(cert).read()
            else:
                raise RuntimeError("Archivos no encontrados: %s, %s" % (privatekey, cert))
        # crear buffers en memoria de la clave privada y certificado:
        key_bio = BIO.MemoryBuffer(privatekey)
        crt_bio = BIO.MemoryBuffer(cert)
        s.load_key_bio(key_bio, crt_bio, callback)  # (desde buffer)
        p7 = s.sign(buf, 0)  # Firmar el buffer
        out = BIO.MemoryBuffer()  # Crear un buffer para la salida
        s.write(out, p7)  # Generar p7 en formato mail
        # Rand.save_file('randpool.dat')         # Guardar el estado del PRNG's

        # extraer el cuerpo del mensaje (parte firmada)
        msg = email.message_from_string(out.read())
        for part in msg.walk():
            filename = part.get_filename()
            if filename == "smime.p7m":  # es la parte firmada?
                return part.get_payload(decode=False)  # devolver CMS
    else:
        # Firmar el texto (tra) usando OPENSSL directamente
        try:
            if sys.platform == "linux2":
                openssl = "openssl"
            else:
                if sys.maxsize <= 2 ** 32:
                    openssl = r"c:\OpenSSL-Win32\bin\openssl.exe"
                else:
                    openssl = r"c:\OpenSSL-Win64\bin\openssl.exe"
            out = Popen([openssl, "smime", "-sign",
                         "-signer", cert, "-inkey", privatekey,
                         "-outform", "DER", "-nodetach"],
                        stdin=PIPE, stdout=PIPE, stderr=PIPE).communicate(tra)[0]
            return b64encode(out)
        except Exception, e:
            if e.errno == 2:
                warnings.warn("El ejecutable de OpenSSL no esta disponible en el PATH")
            raise


class WSAA(WebServiceAFIP):
    "Interfaz para el WebService de Autenticación y Autorización"

    def __init__(self, produccion=False):
        logger.info("Instanciado WSAA - Produccion: %s" %produccion)
        WebServiceAFIP.__init__(self, produccion)

    def CreateTRA(self, service="wsfe", ttl=2400):
        "Crear un Ticket de Requerimiento de Acceso (TRA)"
        tra = create_tra(service, ttl)
        logger.info("TRA Creado: %s" % tra)
        return tra

    def SignTRA(self, tra, cert, privatekey, passphrase=""):
        "Firmar el TRA y devolver CMS"
        logger.info("Generando CMS (firmandos TRA)")
        return sign_tra(str(tra), cert.encode('latin1'), privatekey.encode('latin1'), passphrase.encode("utf8"))

    def Conectar(self):
        wsdl = WSAAURL_PROD if self.produccion else WSAAURL_TEST
        return WebServiceAFIP.Conectar(self, wsdl=wsdl)

    def LoginCMS(self, cms):
        "Obtener ticket de autorización (TA)"
        logger.info("Obteniendo ticket de permiso")
        try:
            xml=et.fromstring(self.client.service.loginCms(in0=str(cms)))
            logger.info("Respuesta: " + et.tostring(xml))
            self.Token = xml[1][0].text
            self.Sign = xml[1][1].text
            self.ExpirationTime = xml[0][4].text
            return True
        except WebFault, e:
            logger.info("Error: %s - %s" %(e.fault.faultcode, e.fault.faultstring))
            self.excCode = e.fault.faultcode
            self.excMsg = e.fault.faultstring
            return False


def obtener_o_crear_permiso(ttl=120, servicio="wsfe", produccion=False):  ##Ruso: Factura electronica
    try:
        permiso = AFIP_Datos_Autenticacion.objects.get(produccion=produccion)
    except AFIP_Datos_Autenticacion.DoesNotExist:
        logger.info("No existe ningun permiso, se generara uno nuevo")
        wsaa = WSAA(produccion=produccion)
        tra = wsaa.CreateTRA(service=servicio, ttl=ttl)
        cert = CERT_FILE_PROD if produccion else CERT_FILE_TEST
        cms = wsaa.SignTRA(tra, cert=cert, privatekey=PRIVATE_KEY_FILE)
        if wsaa.Conectar():
            if wsaa.LoginCMS(cms):
                AFIP_Datos_Autenticacion(sign=wsaa.Sign,
                                         token=wsaa.Token,
                                         expiration=wsaa.ExpirationTime,
                                         produccion=produccion).save()
                return True, wsaa
            else:
                return False, wsaa
        else:
            return False, wsaa

    if permiso.expiration > now():
        logger.info("Existe un permiso cacheado valido")
        wsaa = WSAA()
        wsaa.Sign = permiso.sign
        wsaa.Token = permiso.token
        wsaa.ExpirationTime = permiso.expiration
        return True, wsaa
    else:
        logger.info("Existe un permiso cacheado pero no es valido, se generara uno nuevo")
        wsaa = WSAA(produccion=produccion)
        tra = wsaa.CreateTRA(ttl=ttl, service=servicio)
        cert = CERT_FILE_PROD if produccion else CERT_FILE_TEST
        cms = wsaa.SignTRA(tra, cert=cert, privatekey=PRIVATE_KEY_FILE)
        if wsaa.Conectar():
            if wsaa.LoginCMS(cms):
                permiso.sign = wsaa.Sign
                permiso.token = wsaa.Token
                permiso.expiration = wsaa.ExpirationTime
                permiso.save()
                return True, wsaa
            else:
                return False, wsaa
        else:
            return False, wsaa

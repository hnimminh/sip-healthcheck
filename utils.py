import json
import socket
import yaml
import requests
import time
import logging
import os
from twilio.rest import Client

path = os.path.dirname(os.path.abspath(__file__))

def logged(name):
    my_log = logging.getLogger(name)
    logging.config.dictConfig({
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "simple": {
                "format": "[%(asctime)s] [%(name)s] - [%(levelname)s] - %(message)s"
            }
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "level": "DEBUG",
                "formatter": "simple",
                "stream": "ext://sys.stdout"
            },
            "info_file_handler": {
                "class": "logging.handlers.RotatingFileHandler",
                "level": "INFO",
                "formatter": "simple",
                "filename": "{}/siphealthcheck.log".format(path),
                "maxBytes": 5242880,
                "backupCount": 10,
                "encoding": "utf8"
            },
            "error_file_handler": {
                "class": "logging.handlers.RotatingFileHandler",
                "level": "ERROR",
                "formatter": "simple",
                "filename": "{}/siphealthcheck.log".format(path),
                "maxBytes": 5242880,
                "backupCount": 10,
                "encoding": "utf8"
            }
        },
        "loggers": {
            "my_module": {
                "level": "INFO",
                "handlers": [
                    "console"
                ],
                "propagate": "no"
            }
        },
        "root": {
            "level": "INFO",
            "handlers": [
                "info_file_handler"
            ]
        }
    })

    return my_log


def load_config():
    with open(r'{}/configuration.yml'.format(path)) as file:
        config = yaml.safe_load(file)

    return config


def socket_connection(data, destination_ip, destination_port, source_ip, source_port, transport, timeout):
    if transport.upper() == 'TCP':
        s = socket.socket(
            socket.AF_INET,
            socket.SOCK_STREAM,
            socket.IPPROTO_TCP
        )
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    else:
        s = socket.socket(
            socket.AF_INET,
            socket.SOCK_DGRAM,
            socket.IPPROTO_UDP
        )

    # bind socket
    s.bind((source_ip, source_port))
    s.settimeout(timeout)

    response = None
    error = None
    try:
        s.connect((destination_ip, destination_port))
        s.send(str.encode(data))
        resp = s.recv(65535)

        if resp:
            response = resp.decode()

        # close socket connection
        s.shutdown(1)
        s.close()

    except Exception as e:
        error = e
        raise Exception(e)

    finally:
        return response, error


def notify(category, methods, properties, states):


    name = properties['name']
    transport = properties['transport']
    destination = properties['destination']
    port = properties['port']
    matrix = states['matrix']
    counter = states['counter']

    subject = 'SIP HealthCheck {} on {}'.format(category, name)
    link = '{}://{}:{}'.format(transport, destination, port)
    message = 'Detect {} {} {}'.format(category, name, link)
    content = ('Counter: {} \nMatrix: {}'.format(counter, matrix))


    for method in methods:
        name = method['name']
        if name == 'slack':
            webhook = method['webhook']
            notify2slack(category, webhook, subject, message, content, link)
        if name == 'email':
            sender = method['sender']
            receivers = method['receivers']
            mailgun(sender, receivers, subject, message + "\n" + content, states)
        if name == 'sms':
            sender = method['sender']
            receivers = method['receivers']
            TwilioService().sms(sender, receivers, subject)
        if name == 'call':
            caller = method['caller']
            callee = method['callee']
            # just an example, can create the voice message via xml_content_url when receiving notify call, 
            # or just a call is enough that you aware that is nofication
            xml_content_url = 'http://demo.twilio.com/docs/voice.xml'
            TwilioService().voice(caller, callee, xml_content_url)

def notify2slack(category, webhook, subject, message, content, link):
    app_headers = {'User-Agent': 'ClientX', 'content-type': 'application/json'}
    response = None
    error = None

    try:
        data = {"text": message,
                "username": "SIPHealthCheck",
                "icon_emoji": ":icon:",
                "mrkdwn": True,
                "attachments": [
                    {
                        "color": "#eb0e0e",
                        "title": subject,
                        "title_link": link,
                        "text": content,
                        "footer": "SIPHealthcheck",
                        "footer_icon": "https://",
                        "ts": int(time.time())
                    }
                ]
                }
        response = requests.post(url=webhook, data=json.dumps(data), headers=app_headers)

    except Exception as e:
        error = e
        raise Exception(e)

    finally:
        return response, error

def mailgun(sender, recipients, subject, text_email, html_email):
    api_url = "mailgun_api"
    api_key = "api_key"

    response = None
    error = None
    try:
        response = requests.post(url=api_url,
                                 auth=("api", api_key),
                                 data={
                                     'subject': subject,
                                     'from': sender,
                                     'to': recipients,
                                     'text': text_email,
                                     'html': html_email}
                                 )

    except Exception as e:
        error = e
        raise Exception(e)

    finally:
        return response, error

class TwilioService:
    def __init__(self):
        account_sid = 'account_sid'
        auth_token = 'auth_token'
        self.client = Client(account_sid, auth_token)
        self.logger = logged('TwilioService')

    def sms(self, sender, receiver, content):
        try:
            message = self.client.messages.create(from_=sender, to=receiver, body=content)
            """
            resp = {
                'account_sid': message.account_sid,
                'api_version': message.api_version,
                'body': message.body,
                'date_created': message.date_created,
                'date_updated': message.date_updated,
                'date_sent': message.date_sent,
                'direction': message.direction,
                'error_code': message.error_code,
                'error_message': message.error_message,
                'from_': message.from_,
                'messaging_service_sid': message.messaging_service_sid,
                'num_media': message.num_media,
                'num_segments': message.num_segments,
                'price': message.price,
                'price_unit': message.price_unit,
                'sid': message.sid,
                'status': message.status,
                'subresource_uris': message.subresource_uris,
                'to': message.to,
                'uri': message.uri,
            }
            """
            self.logger.info('TWILIO: {} {}'.format(message.sid, message.status))

        except Exception as e:
            self.logger.info("{}".format(e))

    def voice(self, sender, receiver, url):
        # https://www.twilio.com/docs/voice/quickstart/python#make-an-outgoing-phone-call-with-python
        try:
            call = self.client.calls.create(from_=sender, to=receiver, method='GET', url=url)

            """
            resp = {
                'account_sid': call.account_sid,
                'annotation': call.annotation,
                'answered_by': call.answered_by,
                'api_version': call.api_version,
                'caller_name': call.caller_name,
                'date_created': call.date_created,
                'date_updated': call.date_updated,
                'direction': call.direction,
                'duration': call.duration,
                'end_time': call.end_time,
                'forwarded_from': call.forwarded_from,
                'from_': call.from_,
                'from_formatted': call.from_formatted,
                'group_sid': call.group_sid,
                'parent_call_sid': call.parent_call_sid,
                'phone_number_sid': call.phone_number_sid,
                'price': call.price,
                'price_unit': call.price_unit,
                'sid': call.sid,
                'start_time': call.start_time,
                'status': call.status,
                'subresource_uris': call.subresource_uris,
                'to': call.to,
                'to_formatted': call.to_formatted,
                'uri': call.uri,
            }
            """
            self.logger.info('TWILIO: {} {}'.format(call.sid, call.status))

        except Exception as e:
            self.logger.info("{}".format(e))

import time
import random
import uuid
from threading import Thread
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from utils import socket_connection, load_config, logged, notify

sample_number = 3
configuration = load_config()
version = configuration['application']['version']
application = configuration['application']['name'].replace(' ', '').lower()
domain = configuration['application']['domain']


class SIPProbe(Thread):

    def __init__(self, name, destination_ip, destination_port, transport, ping_interval, ping_timeout,
                 notification_timeout_schedulers, ping_latency, notification_latency_schedulers, notification_methods):

        Thread.__init__(self)
        self.logger = logged(__name__)

        self.name = name

        self.source_ip = ''
        self.source_port = random.randint(10240, 65535)

        self.destination_ip = destination_ip
        self.destination_port = destination_port
        self.transport = transport

        self.ping_interval = ping_interval
        self.timeout = ping_timeout
        self.notification_timeout_schedulers = notification_timeout_schedulers
        self.max_notification_timeout_schedulers = max(notification_timeout_schedulers)
        self.min_notification_timeout_schedulers = min(notification_timeout_schedulers)

        self.ping_latency = ping_latency
        self.notification_latency_schedulers = notification_latency_schedulers
        self.max_notification_latency_schedulers = max(notification_latency_schedulers)
        self.min_notification_latency_schedulers = min(notification_latency_schedulers)

        self.notification_methods = notification_methods

        self.timeout_counter = 0
        self.latency_counter = 0

    def options(self):
        from_tag = str(uuid.uuid4())[:12]
        branch = 'z9hG4bK' + str(uuid.uuid4())[:12]  # https://www.ietf.org/rfc/rfc3261.txt
        call_id = str(uuid.uuid4())
        cseq = random.randint(1, 999999)

        sip_options = (
            'OPTIONS sip:{app_name}@{sip_dest_addr}:{sip_dest_port} SIP/2.0\r\n'
            'Via: SIP/2.0/{transport} {sip_src_addr}:{sip_src_port};branch={branch};rport;alias\r\n'
            'From: <sip:{app_name}@{sip_src_addr}:{sip_src_port}>;tag={from_tag}\r\n'
            'To: <sip:{app_name}@{sip_dest_addr}:{sip_dest_port}>\r\n'
            'Call-ID: {call_id}@{sip_src_addr}\r\n'
            'CSeq: {cseq} OPTIONS\r\n'
            'Contact: <sip:{app_name}@{sip_src_addr}:{sip_src_port}>\r\n'
            'Max-Forwards: 70\r\n'
            'User-Agent: {app_name}_v{version}\r\n'
            'Supported: path, replaces\r\n'
            'Accept: text/plain\r\n'
            'Allow: INVITE, ACK, BYE, CANCEL, OPTIONS, MESSAGE, INFO, UPDATE, NOTIFY\r\n'
            'Content-Length: 0\r\n\r\n').format(
            app_name=application,
            sip_dest_addr=self.destination_ip,
            sip_dest_port=self.destination_port,
            transport=self.transport,
            sip_src_addr=domain,
            sip_src_port=self.source_port,
            branch=branch,
            from_tag=from_tag,
            call_id=call_id,
            cseq=cseq,
            version=version)

        start_time = time.time()
        resp, error = socket_connection(sip_options, self.destination_ip, self.destination_port, self.source_ip,
                                        self.source_port, self.transport, self.timeout)
        latency = round(time.time() - start_time, 3) * 1000

        if resp:
            status_code = resp.split()[1]

            return status_code, latency, resp
        else:
            return None, latency, error

    daemon = True

    def run(self):
        properties = {'name': self.name, 'transport': self.transport, 'destination': self.destination_ip, 'port': self.destination_port}
        states = {'counter': 0, 'matrix': []}
        self.logger.info(
            '[{}] {}://{}:{} interval: {}, timeout: ({} {}), latency: ({} {}) '.format(self.name, self.transport,
                                                                                       self.destination_ip,
                                                                                       self.destination_port,
                                                                                       self.ping_interval, self.timeout,
                                                                                       self.notification_timeout_schedulers,
                                                                                       self.ping_latency,
                                                                                       self.notification_latency_schedulers))
        status_code_list = []
        latency_list = []
        while True:
            start_loop = time.time()
            status_code, latency, message = self.options()

            # timeout
            if status_code == '200':
                self.timeout_counter = 0
                status_code_list = status_code_list[(-1) * self.min_notification_timeout_schedulers:]

                # latency
                if latency < self.ping_latency:
                    self.latency_counter = 0
                    latency_list = latency_list[(-1) * self.min_notification_latency_schedulers:]
                else:
                    self.latency_counter += 1

                latency_list.append(latency)
                if len(latency_list) > sample_number * self.min_notification_latency_schedulers:
                    latency_list = latency_list[(-1) * (sample_number - 1) * self.min_notification_latency_schedulers:]


                states['matrix'] =  latency_list
                states['counter'] =  self.latency_counter

                # latency notify
                if (self.latency_counter in self.notification_latency_schedulers) or (
                        self.latency_counter > 0 and self.latency_counter % self.max_notification_latency_schedulers == 0):
                    
                    notify('Latency', self.notification_methods, properties, states)
                    self.logger.info("{} Latency Notify {}".format(self.name, latency_list))

            else:
                self.timeout_counter += 1

            status_code_list.append(status_code)
            if len(status_code_list) > sample_number * self.min_notification_timeout_schedulers:
                status_code_list = status_code_list[
                                   (-1) * (sample_number - 1) * self.min_notification_timeout_schedulers:]

            states['matrix'] =  status_code_list
            states['counter'] =  self.timeout_counter
            # timeout notify
            if (self.timeout_counter in self.notification_timeout_schedulers) or (
                    self.timeout_counter > 0 and self.timeout_counter % self.max_notification_timeout_schedulers == 0):
                
                notify('Timeout', self.notification_methods, properties, states)
                self.logger.info("{} Timeout Notify {}".format(self.name, status_code_list))

            # summary
            self.logger.info('{} is running... {}_{} {}_{}'.format(self.name, self.timeout_counter, status_code_list,
                                                                   self.latency_counter, latency_list))

            # idle, guarantee ping_interval is precise
            current_loop_ex_time = time.time() - start_loop
            if self.ping_interval > current_loop_ex_time:
                sleep_time = self.ping_interval - current_loop_ex_time
            else:
                sleep_time = self.ping_interval

            time.sleep(sleep_time)

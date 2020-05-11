import time
import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from utils import load_config
from probe import SIPProbe

try:
    configuration = load_config()
    inventory = configuration['inventory']
    default_ping = configuration['ping']
    default_ping_interval = default_ping['interval']
    default_ping_timeout = default_ping['timeout']
    default_ping_latency = default_ping['latency']
    default_notification = configuration['notification']
    default_notification_timeout_schedulers = default_notification['timeout_schedulers']
    default_notification_latency_schedulers = default_notification['latency_schedulers']
    default_notification_methods = default_notification['methods']

    threads = []
    for server in inventory:
        name = server['name']
        host = server['host']
        port = server['port']
        transport = server['transport']
        ping = server.get('ping', default_ping)
        ping_interval = ping.get('interval', default_ping_interval)
        ping_timeout = ping.get('timeout', default_ping_timeout)
        ping_latency = ping.get('latency', default_ping_latency)
        notification = server.get('notification', default_notification)
        notification_timeout_schedulers = notification.get('timeout_schedulers', default_notification_timeout_schedulers)
        notification_latency_schedulers = notification.get('latency_schedulers', default_notification_latency_schedulers)
        notification_methods = notification.get('methods', default_notification_methods)

        instance = SIPProbe(name, host, port, transport, ping_interval, ping_timeout, notification_timeout_schedulers,
                            ping_latency, notification_latency_schedulers, notification_methods)

        threads.append(instance)

    for thread in threads:
        thread.start()

    while True:
        time.sleep(1)

except Exception as error:
    raise Exception(error)

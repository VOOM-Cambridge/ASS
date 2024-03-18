import paho.mqtt.client as mqtt
import multiprocessing
import logging
import zmq
import json
import time
from urllib.parse import urljoin

context = zmq.Context()
logger = logging.getLogger("main.wrapper")


class MQTTServiceWrapper(multiprocessing.Process):
    def __init__(self, config, zmq_conf):
        super().__init__()

        mqtt_conf = config['service_layer']['mqtt']
        self.url = mqtt_conf['broker']
        self.port = int(mqtt_conf['port'])

        self.topic_base = mqtt_conf['base_topic_template']
        self.topic = mqtt_conf['topic']

        self.initial = mqtt_conf['reconnect']['initial']
        self.backoff = mqtt_conf['reconnect']['backoff']
        self.limit = mqtt_conf['reconnect']['limit']
        self.constants = []

        # declarations
        self.zmq_conf = zmq_conf
        self.zmq_out = None
        self.zmq_in = None

    def do_connect(self):
        self.zmq_out = context.socket(self.zmq_conf["out"]['type'])
        if self.zmq_conf["out"]["bind"]:
            self.zmq_out.bind(self.zmq_conf["out"]["address"])
        else:
            self.zmq_out.connect(self.zmq_conf["out"]["address"])

    def mqtt_connect(self, client, first_time=False):
        timeout = self.initial
        exceptions = True
        while exceptions:
            try:
                if first_time:
                    client.connect(self.url, self.port, 60)
                else:
                    logger.error("Attempting to reconnect...")
                    client.reconnect()
                logger.info("Connected!")
                time.sleep(self.initial)  # to give things time to settle
                exceptions = False
            except Exception:
                logger.error(f"Unable to connect, retrying in {timeout} seconds")
                time.sleep(timeout)
                if timeout < self.limit:
                    timeout = timeout * self.backoff
                else:
                    timeout = self.limit

    def on_disconnect(self, client, _userdata, rc):
        if rc != 0:
            logger.error(f"Unexpected MQTT disconnection (rc:{rc}), reconnecting...")
            self.mqtt_connect(client)

    def on_message(self, client, userdata, msg):
        logger.debug("mess recieved form scanner")
        payload = msg.payload.decode("utf-8")
        self.dispatch(payload)

    async def dispatch(self, payload):
        logger.debug(f"ZMQ dispatch of {payload}")
        await self.zmq_out.send_json(payload)

    def run(self):
        self.do_connect()

        client = mqtt.Client()
        # client.on_connect = self.on_connect
        # client.on_message = self.on_message
        client.on_disconnect = self.on_disconnect
        client.on_message = self.on_message
        client.subscribe(self.topic, 1)

        # self.client.tls_set('ca.cert.pem',tls_version=2)
        logger.info(f'connecting to {self.url}:{self.port}')
        self.mqtt_connect(client, True)
        logger.info("Looping and connected")
        client.loop_forever()

import os
import json
import time

from threading import Timer
from dotenv import load_dotenv
from awscrt import mqtt
from awsiot import mqtt_connection_builder

load_dotenv()

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

class MQTTClient:
    def __init__(self, on_message_callback, status_callback=None, device_status_callback=None):
        self.on_message_callback = self._wrap_callback(on_message_callback)
        self.status_callback = status_callback
        self.device_status_callback = device_status_callback
        self.client_id = os.getenv("CLIENT_ID")
        self.topic = os.getenv("TOPIC")
        self.last_message_time = time.time()
        self.timeout_seconds = 5
        self.device_status_timer = None

        self.mqtt_connection = mqtt_connection_builder.mtls_from_path(
            endpoint=os.getenv("AWS_ENDPOINT"),
            cert_filepath=self.get_env_path("CERT_PATH"),
            pri_key_filepath=self.get_env_path("KEY_PATH"),
            client_id=self.client_id,
            ca_filepath=self.get_env_path("CA_PATH"),
            clean_session=False,
            keep_alive_secs=30,
            on_connection_interrupted=self._on_connection_interrupted,
            on_connection_resumed=self._on_connection_resumed,
        )

    def connect_and_subscribe(self):
        print("Connecting to AWS IoT...")
        connect_future = self.mqtt_connection.connect()
        connect_future.result()
        print("✅ Connected!")
        if self.status_callback:
            self.status_callback("MQTT Status: Connected")

        print(f"Subscribing to topic: {self.topic}")
        subscribe_future, _ = self.mqtt_connection.subscribe(
            topic=self.topic,
            qos=mqtt.QoS.AT_LEAST_ONCE,
            callback=self.on_message_callback,
        )

        try:
            subscribe_future.result(timeout=15)
            print("✅ Subscribed!")
        except Exception as e:
            print(f"❌ Subscribe Failed: {e}")

        self._start_device_monitor()

    def disconnect(self):
        print("Disconnecting...")
        self.mqtt_connection.disconnect().result()
        self._cancel_device_monitor()

    def get_env_path(self, var_name):
        val = os.getenv(var_name)
        abs_path = os.path.join(BASE_DIR, val) if val and not os.path.isabs(val) else val
        if not os.path.isfile(abs_path):
            raise FileNotFoundError(f"❌ Cannot find file: {abs_path}")
        return abs_path

    def _on_connection_interrupted(self, connection, error, **kwargs):
        print(f"[⚠️] Connection interrupted: {error}")
        if self.status_callback:
            self.status_callback("MQTT Status: Disconnected")
        if self.device_status_callback:
            self.device_status_callback("Device Status: Unknown")

        print("[🔄] Attempting to reconnect...")
        try:
            reconnect_future = self.mqtt_connection.reconnect()
            reconnect_future.result(timeout=10)
            print("✅ Reconnected successfully")
            if self.status_callback:
                self.status_callback("MQTT Status: Reconnected")
        except Exception as e:
            print(f"[❌] Reconnection failed: {e}")
            if self.status_callback:
                self.status_callback("MQTT Status: Reconnect Failed")
            if self.device_status_callback:
                self.device_status_callback("Device Status: Offline")

    def _on_connection_resumed(self, connection, return_code, session_present, **kwargs):
        print("[🔁] Connection resumed")
        if self.status_callback:
            self.status_callback("MQTT Status: Reconnected")

    def _wrap_callback(self, original_callback):
        def wrapper(topic, payload, **kwargs):
            self.last_message_time = time.time()
            if self.device_status_callback:
                self.device_status_callback("Device Status: Online")
            return original_callback(topic, payload, **kwargs)
        return wrapper

    def _start_device_monitor(self):
        def monitor():
            time_since_last = time.time() - self.last_message_time
            if time_since_last > self.timeout_seconds:
                if self.device_status_callback:
                    self.device_status_callback("Device Status: Offline")
            self.device_status_timer = Timer(1.0, monitor)
            self.device_status_timer.start()

        monitor()

    def _cancel_device_monitor(self):
        if self.device_status_timer:
            self.device_status_timer.cancel()
            self.device_status_timer = None

from paho.mqtt import client as mqtt_client
import random
import time

def create_mqtt_consumer():

    broker = '121.36.170.241'
    port = 1883
    topic = 'testtopic/#'
    client_id = f'python-mqtt-server-{random.randint(0, 1000)}'
    # 如果 broker 需要鉴权，设置用户名密码
    # username = 'test12345'
    # password = 'pwd12345'

    def on_connect(client, userdata, flags, rc):
        if rc == 0:
            print("Connected to MQTT Broker!")
        else:
            print("Failed to connect, return code %d\n", rc)

    def on_message(client, userdata, msg):
        # Print the received timestamped message
        # timestamp = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())
        # print(f"[{timestamp}] Received `{msg.payload.decode()}` from `{msg.topic}` topic")  

        print(f"完整消息对象: {msg}")

    # Set Connecting Client ID
    client = mqtt_client.Client(client_id=client_id)
    # client.tls_set(ca_certs='emqxsl-ca.crt')
    # client.username_pw_set(username, password)
    client.on_connect = on_connect
    client.on_message = on_message
    client.connect(broker, port)

    try:
        client.subscribe(topic)
        client.loop_forever()  # 使用阻塞式循环
    except KeyboardInterrupt:
        print("Exiting...")
    finally:
        client.disconnect()
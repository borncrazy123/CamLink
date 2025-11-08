from paho.mqtt import client as mqtt_client
import random
import time
import os
import threading

def create_mqtt_consumer():
    print("------ 创建 MQTT 消费者 ------")
    broker = '121.36.170.241'
    port = 1883
    topic = [('camlink/+/resp', 2), ('camlink/+/state', 2)]
    client_id = f'python-mqtt-server-{random.randint(0, 1000)}'
    # client_id = 'python-mqtt-server-123'
    # 如果 broker 需要鉴权，设置用户名密码
    username = 'camlink_s_1'
    password = 'camlink_s_1'

    def on_connect(client, userdata, flags, rc):
        if rc == 0:
            print("Connected to MQTT Broker!")
            client.subscribe(topic)
        else:
            print("Failed to connect, return code %d\n", rc)

    def on_message(client, userdata, msg):
        # Print the received timestamped message
        # timestamp = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())
        # print(f"[{timestamp}] Received `{msg.payload.decode()}` from `{msg.topic}` topic")  
        # print(f"完整消息对象: {msg}")

        print("PID:", os.getpid(), "client_id:", client_id, "Topic:", msg.topic, "Message:", msg.payload.decode(),"mid:", msg.mid)

        t = threading.Thread(target=pub_loop, daemon=True)
        t.start()   

    def pub_loop():
        pubResponse = client.publish("camlink/python-mqtt-123/cmd", "Message received, thank you!", qos=2)
        print("pubResponse:", pubResponse)

    # Set Connecting Client ID
    client = mqtt_client.Client(client_id=client_id)
    print("MQTT Client Created with client_id:", client_id)
    # client.tls_set(ca_certs='emqxsl-ca.crt')
    client.username_pw_set(username, password)
    client.on_connect = on_connect
    client.on_message = on_message
    # client.connect(broker, port)

    # try:
        
    #     client.loop_forever()  # 使用阻塞式循环
    #     # client.loop_start()  # 使用非阻塞式循环
    #     # while True:
    #     #     time.sleep(1)
    # except KeyboardInterrupt:
    #     print("Exiting...")
    # finally:
    #     print("Disconnecting from MQTT Broker...")
    #     client.disconnect()

    while True:
        try:
            client.connect(broker, port)
            client.loop_forever()
        except Exception as e:
            print("❌ MQTT 连接失败，5秒后重试:", e)
            time.sleep(5)
        finally:
            print("Disconnecting from MQTT Broker...")
            client.disconnect()
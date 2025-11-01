from app import create_app
import threading
from app.src.mqtt.mqtt_consumer import create_mqtt_consumer

app = create_app()

# --- 后台线程启动mqtt消费者 ---
stop_event = threading.Event()
def background_mqtt_consumer():
    create_mqtt_consumer()
mqtt_thread = threading.Thread(target=background_mqtt_consumer, daemon=True)
mqtt_thread.start()
# --- 后台线程启动mqtt消费者 ---

if __name__ == "__main__":
    try:
        app.run(debug=True)
    except KeyboardInterrupt:
        stop_event.set()
        mqtt_thread.join(timeout=5)  

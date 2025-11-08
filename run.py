from app import create_app
import threading
from app.src.mqtt.mqtt_consumer import create_mqtt_consumer
import os

app = create_app()

if __name__ == "__main__":
    # --- 后台线程启动mqtt消费者 ---
    if os.environ.get('WERKZEUG_RUN_MAIN') == 'true':
        mqtt_thread = threading.Thread(target=create_mqtt_consumer, daemon=True)
        mqtt_thread.start()
    # --- 后台线程启动mqtt消费者 ---

    app.run(debug=True, host='0.0.0.0', port=5001)

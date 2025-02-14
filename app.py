from flask import Flask, request, jsonify
from datetime import datetime, timedelta

app = Flask(__name__)

# Simulating stopwatch state (normally you'd use a database)
stopwatch_state = {
    "project_name": "",
    "minutes": 0,
    "precise_seconds": 0,
    "is_running": False,
    "last_started": None
}

@app.route('/start', methods=['POST'])
def start_timer():
    global stopwatch_state
    if not stopwatch_state["is_running"]:
        stopwatch_state["is_running"] = True
        stopwatch_state["last_started"] = datetime.now().isoformat()
    return jsonify(stopwatch_state)

@app.route('/stop', methods=['POST'])
def stop_timer():
    global stopwatch_state
    if stopwatch_state["is_running"]:
        stopwatch_state["is_running"] = False
    return jsonify(stopwatch_state)

@app.route('/status', methods=['GET'])
def get_status():
    return jsonify(stopwatch_state)

if __name__ == '__main__':
    app.run(debug=True)

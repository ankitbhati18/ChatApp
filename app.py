from flask import Flask, request
from flask_socketio import SocketIO, join_room, leave_room, send
import random
from string import ascii_uppercase

app = Flask(__name__)
app.config["SECRET_KEY"] = "ccyjv"
socketio = SocketIO(app, cors_allowed_origins="*")  # Allow all origins for dev; configure in prod

rooms = {}  # e.g. rooms = {"ROOMCODE": {"members": 0, "messages": []}}

def generate_code(length=4):
    while True:
        code = ''.join(random.choice(ascii_uppercase) for _ in range(length))
        if code not in rooms:
            return code

@app.route('/api/create_room', methods=['POST'])
def create_room():
    room_code = generate_code()
    rooms[room_code] = {"members": 0, "messages": []}
    return {"room": room_code}, 201

@app.route('/api/join_room', methods=['POST'])
def join_room_api():
    room_code = request.json.get('room')
    if room_code in rooms:
        return {"message": "Joined room successfully."}, 200
    return {"message": "Room not found."}, 404

@socketio.on('join_room')
def handle_join(data):
    room = data.get('room')
    name = data.get('name')
    if not room or not name:
        return
    join_room(room)
    if room not in rooms:
        rooms[room] = {"members": 0, "messages": []}
    rooms[room]["members"] += 1
    # Broadcast join message to other users in room
    send({"name": name, "message": "has joined the room."}, to=room)
    socketio.emit('user_joined', {"name": name, "message": f"{name} has joined the room."}, to=room)
    print(f"{name} joined room {room}")
@socketio.on('leave_room')
def handle_leave(data):
    room = data.get('room')
    name = data.get('name')
    if not room or not name:
        return
    leave_room(room)
    if room in rooms:
        rooms[room]["members"] -= 1
        if rooms[room]["members"] <= 0:
            del rooms[room]
    socketio.emit('user_left', {"name": name, "message": f"{name} has left the room."}, to=room)
    print(f"{name} left room {room}")
    
@socketio.on('message')


def handle_message(data):
    room = data.get('room')
    if not room or room not in rooms:
        return
    msg_content = data.get('data')
    name = data.get('name', 'Anonymous')
    message_data = {"name": name, "message": msg_content}
    rooms[room]["messages"].append(message_data)
    send(message_data, to=room)
    print(f"{name} said: {msg_content}")
if __name__ == "__main__":
    socketio.run(app, debug=True)

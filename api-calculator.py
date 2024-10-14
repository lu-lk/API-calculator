from flask import Flask, request, jsonify

app = Flask(__name__)

@app.route('/')
def home():
    return jsonify({"message": "Welcome to Flask Calculator API"})

@app.route('/add', methods=['GET'])
def add():
    a = float(request.args.get('a'))
    b = float(request.args.get('b'))
    result = a + b
    return jsonify({"result": result})

@app.route('/subtract', methods=['GET'])
def subtract():
    a = float(request.args.get('a'))
    b = float(request.args.get('b'))
    result = a - b
    return jsonify({"result": result})

@app.route('/multiply', methods=['GET'])
def multiply():
    a = float(request.args.get('a'))
    b = float(request.args.get('b'))
    result = a * b
    return jsonify({"result": result})

@app.route('/divide', methods=['GET'])
def divide():
    a = float(request.args.get('a'))
    b = float(request.args.get('b'))
    if b == 0:
        return jsonify({"error": "Division by zero is not allowed"}), 400
    result = a / b
    return jsonify({"result": result})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5555)

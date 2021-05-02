import flask
import os

app = flask.Flask(__name__)


@app.route("/")
def hello_payment():
    resp = {
        "message": "Hello from payment service in docker !!!",
        "service_name": "payment"
    }
    schema = {
        'status': 200,
        'message': resp
    }
    return flask.jsonify(schema)


@app.route("/api/payment")
def get_payment():
    resp = {
        "message": "Hello from payment service in docker !!!",
        "service_name": "payment"
    }
    schema = {
        'status': 200,
        'message': resp
    }
    return flask.jsonify(schema)


@app.route("/api/payment/history")
def get_payment_history():
    resp = {
        "message": "Internal Server Error from payment !!!",
        "service_name": "payment"
    }
    schema = {
        'status': 500,
        'message': resp
    }
    return flask.jsonify(schema)


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 4000))
    app.run(debug=True, host='0.0.0.0', port=port)

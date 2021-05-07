import flask
import os

app = flask.Flask(__name__)


@app.route("/")
def hello_order():
    resp = {
        "message": "Hello from order service in docker !!!",
        "service_name": "order"
    }
    schema = {
        'status': 200,
        'message': resp
    }
    return flask.jsonify(schema)


@app.route("/api/orders")
def get_orders():
    resp = {
        "message": "Hello from order service in docker !!!",
        "service_name": "order"
    }
    schema = {
        'status': 200,
        'message': resp
    }
    return flask.jsonify(schema)


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(debug=True, host='0.0.0.0', port=port)

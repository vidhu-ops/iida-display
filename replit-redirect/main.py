from flask import Flask, redirect, request

app = Flask(__name__)
TARGET = "https://iida-display-nu.vercel.app"


@app.route("/", defaults={"path": ""})
@app.route("/<path:path>")
def redirect_to_vercel(path):
    dest = TARGET if not path else f"{TARGET}/{path}"
    if request.query_string:
        dest = f"{dest}?{request.query_string.decode()}"
    return redirect(dest, code=301)

from flask import redirect, render_template, session
from functools import wraps


def apology(message, code=400):
    image_src = ""
    print("Username" in message)
    if "Username" in message:
        image_src = "https://api.memegen.link/images/spiderman/username_already_exists.jpg?watermark=MemeComplete.com&token=mwsmz4o16r1wticvvdhb"
    elif "empty" in message:
        image_src = "https://api.memegen.link/images/mordor/one_does_not_simply/truncate_the_password_fields.jpg?watermark=MemeComplete.com&token=08ctdp38ly830pj22koi"
    elif "match" in message:
        image_src = "https://api.memegen.link/images/grumpycat/not_funny/passwords_do_not_match.jpg?watermark=MemeComplete.com&token=upkkuu9kcdnif4yhhz3x"
    return render_template(
        "apology.html", top=code, bottom=message, image_src=image_src
    )


def login_required(f):
    """
    Decorate routes to require login.

    https://flask.palletsprojects.com/en/1.1.x/patterns/viewdecorators/
    """

    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("user_id") is None:
            return redirect("/login")
        return f(*args, **kwargs)

    return decorated_function

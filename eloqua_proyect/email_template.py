def load_email_template():
    with open("email.html", "r", encoding="utf-8") as f:
        return f.read()
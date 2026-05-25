import re


def clean_form_errors(form):
    message = " ".join(error for errors in form.errors.values() for error in errors)
    return clean_message(message)


def clean_message(message):
    message = re.sub(r"[^A-Za-z\s]", " ", str(message))
    return " ".join(message.split())

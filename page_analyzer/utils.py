import validators


def custom_validators_url(url):
    if len(url) <= 255:
        return validators.url(url)
    else:
        return False

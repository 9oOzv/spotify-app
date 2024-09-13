from base64 import b64encode


def b64(s: str) -> str:
    return b64encode(s.encode()).decode()


def truncate(value, length: int):
    text = str(value)
    return (
        text[:length - 3] + '...'
        if len(text) > length - 3
        else value
    )

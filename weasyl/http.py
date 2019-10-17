


def get_headers(wsgi_env):
    """
    Extracts HTTP_* variables from a WSGI environment as
    title-cased header names.
    """
    return {
        key[5:].replace('_', '-').title(): value
        for key, value in wsgi_env.items() if key.startswith('HTTP_')}

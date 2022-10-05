from uuid import uuid4


# randomize name
def randomize_name(name: str) -> str:
    """
    add a random suffix to a name

    :param name:
    :return: name with random suffix
    """
    name = name.replace('.', '_')
    random_id = str(uuid4()).replace('-', '_')

    return f'_{name}_{random_id}'

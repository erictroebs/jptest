from typing import List, Dict, Tuple, Union
from uuid import uuid4


# randomize name
def randomize_name(name: str) -> str:
    """
    add a random suffix to a name

    :param name:
    :return: name with random suffix
    """
    random_id = str(uuid4()).replace('-', '_')
    return f'_{name}_{random_id}'


# parse outputs
CELL_DATA = List[Tuple[str, Union[str, Dict]]]
CELL_STREAM = Union[str, None]
# CELL_ERROR = Union[Tuple[str, str, List], None]
CELL_EXECUTION_RESULT = Tuple[CELL_DATA, CELL_STREAM, CELL_STREAM, CELL_DATA]


def parse_outputs(cell: Dict):
    """
    extract output data from a cell

    :param cell: cell from jupyter notebook
    :return: tuple with different output types
    """
    execute_result: CELL_DATA = []
    stream_stdout: CELL_STREAM = None
    stream_stderr: CELL_STREAM = None
    display_data: CELL_DATA = []
    # error: CELL_ERROR = None

    for o in cell['outputs']:
        if o['output_type'] == 'execute_result':
            for k, v in o['data'].items():
                execute_result.append((k, v))
        elif o['output_type'] == 'stream' and o['name'] == 'stdout':
            stream_stdout = o['text']
        elif o['output_type'] == 'stream' and o['name'] == 'stderr':
            stream_stderr = o['text']
        elif o['output_type'] == 'display_data':
            for k, v in o['data'].items():
                display_data.append((k, v))
        # elif o['output_type'] == 'error':
        #     error = o['ename'], o['evalue'], o['traceback']
        else:
            raise AssertionError

    return execute_result, stream_stdout, stream_stderr, display_data  # , error

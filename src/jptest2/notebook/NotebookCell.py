from asyncio import Lock
from typing import List, Tuple, Union, Dict

from nbclient import NotebookClient
from nbformat import NotebookNode


class NotebookCell:
    CELL_DATA = List[Tuple[str, Union[str, Dict]]]
    CELL_STREAM = Union[str, None]
    # CELL_ERROR = Union[Tuple[str, str, List], None]
    CELL_EXECUTION_RESULT = Tuple[CELL_DATA, CELL_STREAM, CELL_STREAM, CELL_DATA]

    def __init__(self, nb: NotebookNode, nc: NotebookClient, lock: Lock, idx: int):
        self._nb: NotebookNode = nb
        self._nc: NotebookClient = nc
        self._lock: Lock = lock
        self._idx: int = idx

    @property
    def _cell(self) -> NotebookNode:
        return self._nb.cells[self._idx]

    @property
    def type(self) -> str:
        return self._cell['cell_type']

    @property
    def tags(self) -> List[str]:
        if 'tags' in self._cell['metadata']:
            return self._cell['metadata']['tags']
        else:
            return []

    async def execute(self) -> "NotebookCell":
        """
        execute this cell in notebook context

        :return: self
        """
        async with self._lock:
            await self._nc.async_execute_cell(cell=self._cell, cell_index=self._idx)
            return self

    def output(self) -> CELL_EXECUTION_RESULT:
        """
        extract output data from a cell

        :return: tuple with different output types
        """
        execute_result: NotebookCell.CELL_DATA = []
        stream_stdout: NotebookCell.CELL_STREAM = None
        stream_stderr: NotebookCell.CELL_STREAM = None
        display_data: NotebookCell.CELL_DATA = []
        # error: CELL_ERROR = None

        for o in self._cell['outputs']:
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

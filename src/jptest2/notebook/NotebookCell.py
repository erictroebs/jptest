from typing import List, Tuple, Union, Dict, Callable, Awaitable

from nbformat import NotebookNode

from .NotebookError import NotebookError


class NotebookCell:
    CELL_DATA = List[Tuple[str, Union[str, Dict]]]
    CELL_STREAM = Union[str, None]
    # CELL_ERROR = Union[Tuple[str, str, List], None]
    CELL_EXECUTION_RESULT = Tuple[CELL_DATA, CELL_STREAM, CELL_STREAM, CELL_DATA]

    def __init__(self, nb: NotebookNode, ce: Callable[["NotebookCell"], Awaitable], idx: int):
        self._nb: NotebookNode = nb
        self._ce: Callable[[NotebookCell], Awaitable] = ce
        self.idx: int = idx
        self.last_execution_result = None

    @property
    def raw_cell(self) -> NotebookNode:
        return self._nb.cells[self.idx]

    @property
    def type(self) -> str:
        """
        cell type

        :return:
        """
        return self.raw_cell['cell_type']

    @property
    def tags(self) -> List[str]:
        """
        list of tags

        :return:
        """
        if 'tags' in self.raw_cell['metadata']:
            return self.raw_cell['metadata']['tags']
        else:
            return []

    @property
    def source(self) -> str:
        return self.raw_cell['source']

    async def execute(self) -> "NotebookCell":
        """
        execute this cell in notebook context

        :return: self
        """
        self.last_execution_result = await self._ce(self)
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

        for o in self.raw_cell['outputs']:
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
            elif o['output_type'] == 'error':
                raise NotebookError(o['ename'], o['evalue'], o['traceback'])
            else:
                raise AssertionError

        return execute_result, stream_stdout, stream_stderr, display_data  # , error

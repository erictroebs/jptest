import asyncio
from inspect import getsource
from os import PathLike
from typing import Callable

import nbformat
from nbclient import NotebookClient
from nbformat import NotebookNode
from nbformat.v4 import new_code_cell

from .NotebookFunctionReplacement import NotebookFunctionReplacement
from .NotebookFunctionWrapper import NotebookFunctionWrapper
from .NotebookReference import NotebookReference
from .util import *


class Notebook:
    """
    class for async interaction with notebooks
    """

    def __init__(self, notebook: Union[str, PathLike], timeout: int = 120):
        """
        :param notebook: notebook path
        :param timeout: timeout in seconds
        """
        self._nb: NotebookNode = nbformat.read(notebook, as_version=4)
        self._nc: NotebookClient = NotebookClient(self._nb, kernel_name='python3', timeout=timeout)

    async def __aenter__(self) -> "Notebook":
        """
        initialize kernel

        :return: self
        """
        await self._nc.async_setup_kernel(cleanup_kc=False).__aenter__()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """
        clear kernel

        :param exc_type:
        :param exc_val:
        :param exc_tb:
        """
        await self._nc._async_cleanup_kernel()

    def ref(self, name: str) -> NotebookReference:
        """
        get a reference to an object inside the notebook context

        :param name: name of object
        :return: NotebookReference
        """
        return NotebookReference(self, name)

    def refs(self, *names: str) -> Tuple[NotebookReference, ...]:
        """
        get multiple references to objects inside the notebook context

        :param names: list of names
        :return: list of NotebookReference
        """
        return tuple(self.ref(n) for n in names)

    async def get(self, name: str) -> NotebookReference:
        """
        copy object to a random name and return a reference

        :param name: name of object
        :return: NotebookReference
        """
        return await self.ref(name).copy()

    async def gets(self, *names: str) -> Tuple[NotebookReference, ...]:
        """
        copy multiple objects to random names and return references

        :param names: list of names
        :return: list of NotebookReference
        """
        return await asyncio.gather(*(self.get(n) for n in names))

    async def execute_code(self, code: str) -> CELL_EXECUTION_RESULT:
        """
        execute code in notebook context

        :param code: code string
        :return: cell output after execution
        """
        # create new code cell
        cell = new_code_cell(code)

        # insert into notebook
        insert_index = len(self._nb.cells)
        self._nb.cells.append(cell)

        # execute cell
        await self._nc.async_execute_cell(cell=cell, cell_index=insert_index)

        # parse output
        return parse_outputs(cell)

    async def execute_cells(self, *tag: str) -> List[CELL_EXECUTION_RESULT]:
        """
        Executes all code cells matching one of the given tags. Executes every code cell if no tag is given.

        :param tag: cell tags
        :return:
        """
        result: List[CELL_EXECUTION_RESULT] = []

        for index, cell in enumerate(self._nb.cells):
            if cell['cell_type'] != 'code':
                continue

            if len(tag) == 0 or 'tags' in cell['metadata'] and any([t in cell['metadata']['tags'] for t in tag]):
                await self._nc.async_execute_cell(cell=cell, cell_index=index)
                result.append(parse_outputs(cell))

        return result

    async def execute_fun(self, fun: Callable) -> CELL_EXECUTION_RESULT:
        """
        strip header from function and execute in notebook context

        :param fun: function
        :return:
        """

        # get function code
        code = getsource(fun)

        # split lines
        loc = code.split('\n')

        # strip function header
        loc = loc[1:]

        # remove return statement and subsequent lines
        for i in range(len(loc)):
            if loc[i].lstrip().startswith('return '):
                loc[i] = ''.join(loc[i].split('return ', maxsplit=1))
                loc = loc[:i + 1]
                break

        # recreate code from locs
        code = '\n'.join(loc)

        # execute code
        return await self.execute_code(code)

    async def inject_fun(self, fun: Callable) -> NotebookReference:
        """
        inject function into notebook and return reference

        :param fun: function
        :return:
        """
        code = getsource(fun)
        await self.execute_code(code)

        fun_name = fun.__name__
        if fun_name == '<lambda>':
            fun_name = code.split('=')[0].strip()

        return self.ref(fun_name)

    def replace_fun(self, fun_name: str, replacement: Callable) -> NotebookFunctionReplacement:
        """
        replace a function

        :param fun_name: function to replace in notebook
        :param replacement: function to use as replacement
        :return: instance of NotebookFunctionReplacement
        """
        return NotebookFunctionReplacement(self, fun_name, replacement)

    def track_fun(self, fun_name: str, *parameters: str,
                  all_parameters: bool = False, return_values: bool = True) -> NotebookFunctionWrapper:
        """
        wrap a function to track calls

        :param fun_name: function name
        :param parameters: list of parameters as str (name) or tuple (name, position)
        :param all_parameters: include all parameters (ignore argument `parameters`)
        :param return_values: include return values
        :return: instance of NotebookFunctionWrapper
        """
        return NotebookFunctionWrapper(self, fun_name, *parameters,
                                       all_parameters=all_parameters, return_values=return_values)

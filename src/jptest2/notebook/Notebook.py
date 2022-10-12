import asyncio
import pickle
from inspect import getsource
from os import PathLike
from typing import Callable, List, Tuple, Union, Optional, Any

import nbformat
from nbclient import NotebookClient
from nbformat import NotebookNode
from nbformat.v4 import new_code_cell

from .NotebookCell import NotebookCell
from .NotebookFunctionReplacement import NotebookFunctionReplacement
from .NotebookFunctionWrapper import NotebookFunctionWrapper
from .NotebookReference import NotebookReference


class Notebook:
    """
    class for async interaction with notebooks
    """

    def __init__(self, notebook: Union[str, PathLike], execute: bool = False, timeout: int = 120):
        """
        :param notebook: notebook path
        :param execute: execute all cells in `__aenter__`
        :param timeout: timeout per cell in seconds
        """
        self._nb: NotebookNode = nbformat.read(notebook, as_version=4)
        self._nc: NotebookClient = NotebookClient(self._nb, kernel_name='python3', timeout=timeout)
        self._lock: asyncio.Lock = asyncio.Lock()
        self._execute: bool = execute

    async def __aenter__(self) -> "Notebook":
        """
        initialize kernel

        :return: self
        """
        await self._nc.async_setup_kernel(cleanup_kc=False).__aenter__()

        if self._execute:
            await self.execute_cells()

        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """
        clear kernel

        :param exc_type:
        :param exc_val:
        :param exc_tb:
        """
        await self._nc._async_cleanup_kernel()

    def __getattr__(self, name: str) -> NotebookReference:
        """
        alias for `ref`

        :param name: name of object
        :return: NotebookReference
        """
        return self.ref(name)

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
        return await asyncio.gather(*[self.get(n) for n in names])

    async def execute_code(self, code: str) -> NotebookCell:
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
        nb_cell = NotebookCell(self._nb, self._nc, self._lock, insert_index)
        await nb_cell.execute()

        # parse output
        return nb_cell

    @property
    def cells(self) -> List[NotebookCell]:
        """
        get a list of all cells

        :return: list of NotebookCell
        """
        return [NotebookCell(self._nb, self._nc, self._lock, i) for i in range(len(self._nb.cells))]

    async def execute_cells(self, *tag: str, from_tag: str = None, to_tag: str = None) -> List[NotebookCell]:
        """
        execute code cells
          - all cells by default
          - matching at least one of the given tags if given
          - only between first occurrence of `from_tag` to first occurrence of `to_tag` if given

        :param tag: cell tags
        :param from_tag: start execution after first occurrence
        :param to_tag: stop execution after first occurrence
        :return:
        """
        result: List[NotebookCell] = []

        start_tag_found = False
        end_tag_found = False

        for cell in self.cells:
            if from_tag in cell.tags:
                start_tag_found = True
            if to_tag in cell.tags:
                end_tag_found = True

            if cell.type != 'code' or (from_tag is not None and not start_tag_found):
                continue

            if len(tag) == 0 or any([t in cell.tags for t in tag]):
                await cell.execute()
                result.append(cell)

            if end_tag_found:
                break

        return result

    async def store(self, name: str, value: Any) -> NotebookReference:
        encoded_value = pickle.dumps(value)
        await self.execute_code(f'''
            import pickle
            {name} = pickle.loads({encoded_value})
        ''')

        return self.ref(name)

    async def execute_fun(self, fun: Callable) -> NotebookCell:
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
        i: int = 0
        inner_fun: Optional[int] = None
        return_found: Optional[int] = None

        while i < len(loc):
            # strip line and calculate indent
            line = loc[i].lstrip()
            indent = len(loc[i]) - len(line)

            # remove empty lines
            if line == '':
                del loc[i]
                continue

            # compare indent
            if inner_fun is not None and indent <= inner_fun:
                inner_fun = None

            if return_found is not None and indent < return_found:
                return_found = None

            # skip inner functions
            if line.startswith('def ') or line.startswith('async def '):
                inner_fun = indent

            if inner_fun:
                i += 1
                continue

            # remove return statements and lines in block after
            if return_found:
                del loc[i]
                continue

            if line.startswith('return '):
                loc[i] = f'{" " * indent}{line[7:]}'
                return_found = indent

            i += 1

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

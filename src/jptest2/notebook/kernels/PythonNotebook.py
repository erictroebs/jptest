import asyncio
import pickle
from asyncio import Lock
from inspect import getsource
from os import PathLike
from typing import Callable, Tuple, Union, Optional, Any

from nbclient import NotebookClient

from .. import Notebook
from ..NotebookCell import NotebookCell
from ..NotebookFunctionReplacement import NotebookFunctionReplacement
from ..NotebookFunctionWrapper import NotebookFunctionWrapper
from ..NotebookReference import NotebookReference
from ..util import randomize_name


class PythonNotebook(Notebook):
    def __init__(self, notebook: Union[str, PathLike], execute: bool = False, timeout: int = 120):
        super().__init__(notebook, self.__execute_cell, execute)

        self._nc: NotebookClient = NotebookClient(self._nb, kernel_name='python3', timeout=timeout)
        self._lock: Lock = Lock()

    async def __aenter__(self) -> "Notebook":
        """
        initialize kernel

        :return: self
        """
        await self._nc.async_setup_kernel(cleanup_kc=False).__aenter__()
        await super().__aenter__()

        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """
        clear kernel

        :param exc_type:
        :param exc_val:
        :param exc_tb:
        """
        await super().__aexit__(exc_type, exc_val, exc_tb)
        await self._nc._async_cleanup_kernel()

    async def __execute_cell(self, cell: NotebookCell):
        async with self._lock:
            await self._nc.async_execute_cell(cell.raw_cell, cell_index=cell.idx)

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

    async def store(self, value: Any, name: str = None) -> NotebookReference:
        """
        store a value in the notebook context.
        A random name is chosen if no custom name is given.

        :param value: variable value in notebook
        :param name: variable name in notebook
        :return: reference to created variable
        """
        # choose a random name if no custom name is provided
        if name is None:
            name = randomize_name('stored')

        # handle references
        if isinstance(value, NotebookReference):
            # handle local references (from same notebook)
            if value.is_from(self):
                return await value.copy(name)

            # handle remote references (from other notebook)
            else:
                encoded_value = await value.receive(deserialize=False)

        # handle any other values
        else:
            encoded_value = pickle.dumps(value)

        # send to notebook
        await self.execute_code(f'''
            import pickle
            {name} = pickle.loads({encoded_value})
        ''')

        # return reference
        return self.ref(name)

    async def stores(self, **kwargs) -> Tuple[NotebookReference, ...]:
        """
        store multiple values in the notebook context

        :param kwargs:
        :return: tuple of references
        """
        return await asyncio.gather(*[self.store(v, k) for k, v in kwargs.items()])

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

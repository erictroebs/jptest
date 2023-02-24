from typing import List, Set, Optional

from . import Notebook
from .NotebookFunctionCall import NotebookFunctionCall
from .NotebookReference import NotebookReference
from .util import randomize_name


class NotebookFunctionWrapper:
    """
    wraps a function and allows to receive tracked parameters
    """

    def __init__(self, nb: Notebook, fun_name: str,
                 *parameters: str, all_parameters: bool = False, return_values: bool = True):
        """
        :param nb:
        :param fun_name: function name to replace
        :param parameters: parameter names to track
        :param all_parameters: include all parameters (ignore parameters)
        :param return_values: include return values (None otherwise)
        """
        self._nb = nb
        self._fun_name = fun_name

        self._parameters: Set[str] = set(parameters)
        self._all_parameters: bool = all_parameters
        self._return_values: bool = return_values

    async def __aenter__(self) -> "NotebookFunctionWrapper":
        """
        replace function with wrapper

        :return: self
        """
        # store backup
        self._backup: NotebookReference = await self._nb.get(self._fun_name)

        # inject tracker and store reference
        class_name = randomize_name('Track')
        wrapper_name = randomize_name('track')

        await self._nb.execute_code(f'''
            class {class_name}:
                def __init__(self, fun):
                    # store properties
                    self._include_parameters = {self._parameters}
                    self._include_all_parameters = {self._all_parameters}
                    self._include_return_values = {self._return_values}
            
                    # analyse `fun`
                    self.fun = fun
            
                    self._fun_default_values = {{}}
                    self._fun_positions = []
                    self._fun_names = set()
                    self._fun_var_positional = None
                    self._fun_var_keyword = None
            
                    import inspect
                    from inspect import Signature, Parameter
                    signature: Signature = inspect.signature(fun)
            
                    for index, param in enumerate(signature.parameters.values()):
                        if param.default is not Parameter.empty:
                            self._fun_default_values[param.name] = param.default
                        if param.kind == Parameter.POSITIONAL_OR_KEYWORD or param.kind == Parameter.POSITIONAL_ONLY:
                            self._fun_positions.append(param.name)
                        if param.kind == Parameter.POSITIONAL_OR_KEYWORD or param.kind == Parameter.KEYWORD_ONLY:
                            self._fun_names.add(param.name)
                        if param.kind == Parameter.VAR_POSITIONAL:
                            self._fun_var_positional = index
                            self._fun_positions.append(param.name)
                        if param.kind == Parameter.VAR_KEYWORD:
                            self._fun_var_keyword = param.name
            
                    # store calls array
                    self.calls = []
            
                def __call__(self):
                    def wrapper_fun(*args, **kwargs):
                        call_params = {{}}
            
                        # extract args
                        for i, val in enumerate(args):
                            name = self._fun_positions[min(i, len(self._fun_positions) - 1)]
        
                            if self._fun_var_positional is not None and i >= self._fun_var_positional:
                                if name not in call_params:
                                    call_params[name] = []
        
                                call_params[name].append(val)
        
                            else:
                                call_params[name] = val
            
                        # extract kwargs
                        for name, val in kwargs.items():
                            if name in self._fun_names:
                                call_params[name] = val
                            elif self._fun_var_keyword is not None:
                                if self._fun_var_keyword not in call_params:
                                    call_params[self._fun_var_keyword] = {{}}
            
                                call_params[self._fun_var_keyword][name] = val
            
                        # insert default values
                        for name, val in self._fun_default_values.items():
                            if name not in call_params:
                                call_params[name] = val
            
                        # apply filter
                        if not self._include_all_parameters:
                            for key in list(call_params):
                                print(key, self._include_parameters)
                                if key not in self._include_parameters:
                                    del call_params[key]
            
                        # get result
                        result = self.fun(*args, **kwargs)
            
                        # append output
                        if self._include_return_values:
                            self.calls.append((call_params, result))
                        else:
                            self.calls.append((call_params, None))
            
                        # return fun result
                        return result
            
                    return wrapper_fun
            
                def clear(self):
                    self.calls = []
            
            {wrapper_name} = {class_name}({self._fun_name})
            {self._fun_name} = {wrapper_name}()
        ''')

        self._wrapper: NotebookReference = self._nb.ref(wrapper_name)

        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """
        replace wrapper with original function

        :param exc_type:
        :param exc_val:
        :param exc_tb:
        :return:
        """
        await self._nb.execute_code(f'''
            {self._fun_name} = {self._backup.name}
        ''')

    async def clear(self):
        """
        clear stored calls

        :return:
        """
        await self._wrapper.clear().execute()

    async def receive(self) -> List[NotebookFunctionCall]:
        """
        receive a list of all calls

        :return: list of NotebookFunctionCall
        """
        return list(map(
            lambda c: NotebookFunctionCall(self._nb, self._fun_name, *c),
            await self._wrapper.calls.receive()
        ))

    def __await__(self):
        return self.receive().__await__()

    async def receive_first(self) -> Optional[NotebookFunctionCall]:
        """
        receive the first call made (if any)

        :return: NotebookFunctionCall
        """
        if await self._wrapper.calls.len() > 0:
            return NotebookFunctionCall(self._nb, self._fun_name, *(await self._wrapper.calls[0].receive()))

    async def receive_last(self) -> Optional[NotebookFunctionCall]:
        """
        receive the last call made (if any)

        :return: NotebookFunctionCall
        """
        if await self._wrapper.calls.len() > 0:
            return NotebookFunctionCall(self._nb, self._fun_name, *(await self._wrapper.calls[-1].receive()))

import functools
from types import FunctionType
from typing import List, Union, Tuple, Dict, Any

from testbook import testbook

from .JPTestBook import JPTestBook
from .JPTestParams import JPTestParams

TRACK_TYPE = Dict[str,
                  Union[Tuple[str, int],
                        List[Tuple[str, int]]]]
EXECUTE_TYPE = Union[Tuple[str],
                     Tuple[str, str],
                     str,
                     FunctionType,
                     List['EXECUTE_TYPE'],
                     Dict[str, Union['EXECUTE_TYPE', TRACK_TYPE]]]


class JPTest(testbook):
    def __init__(self, nb: str, execute: EXECUTE_TYPE = None):
        super().__init__(nb, execute)
        self._jtb = JPTestBook(self.client)

    def _prepare_recursive(self, item: EXECUTE_TYPE) -> List[Dict[str, Any]]:
        extracted = []

        if isinstance(item, dict):
            # create function wrappers
            wrappers = {}

            if 'track' in item:
                for key in item['track']:
                    class_name = self._jtb.random_id('Track')
                    variable_name = self._jtb.random_id('track')

                    wrappers[key] = self._jtb.inject(f'''
                        class {class_name}:
                            def __init__(self, fun):
                                self._calls = []

                                def patch(*args, **kwargs):
                                    result = fun(*args, **kwargs)
                                    self._calls.append((args, kwargs, result))

                                    return result

                                self.fun = fun
                                self.patch = patch

                            def extract_parameters(self, params):
                                result = []
                                for args, kwargs, _ in self._calls:
                                    call_result = {{}}
                                    result.append(call_result)

                                    for name, pos in params:
                                        if name in kwargs:
                                            call_result[name] = kwargs[name]
                                        elif pos < len(args):
                                            call_result[name] = args[pos]

                                return result

                        {variable_name} = {class_name}({key})
                        {key} = {variable_name}.patch
                    ''', variable_name)

            # execute cells
            sub_extracted = self._prepare_recursive(item['cells'])

            # extract parameters
            for key, reference in wrappers.items():
                parameters = item['track'][key]
                if not isinstance(parameters, list):
                    parameters = [parameters]

                values = reference.extract_parameters(parameters)
                params = JPTestParams(key, parameters, values)

                extracted.append(params)

            # add extracted parameters from sub-executions
            for ep in sub_extracted:
                extracted.append(ep)

            # remove wrappers
            for key, reference in reversed(wrappers.items()):
                self._jtb.inject(f'''
                    {key} = {reference.name}.fun
                ''')

        elif isinstance(item, tuple):
            if len(item) == 2:
                self.client.execute_cell(slice(item[0], item[1]))
            elif len(item) == 1:
                self.client.execute_cell(item[0])
            else:
                raise ValueError('unsupported tuple length')

        elif isinstance(item, str):
            self.client.inject(item)

        elif isinstance(item, FunctionType):
            item(self.client)

        elif isinstance(item, list):
            for i in item:
                for ep in self._prepare_recursive(i):
                    extracted.append(ep)

        else:
            raise ValueError(f'unsupported parameter type {type(item)}')

        return extracted

    def __call__(self, func):
        @functools.wraps(func)
        def wrapper():
            with self.client.setup_kernel():
                if self.execute is None:
                    tracked_parameters = []
                else:
                    tracked_parameters = self._prepare_recursive(self.execute)

                func(self._jtb, *tracked_parameters)

        wrapper.patchings = [self]
        return wrapper

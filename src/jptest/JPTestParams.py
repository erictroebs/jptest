from typing import List, Dict, Any, Tuple

from testbook.reference import TestbookObjectReference


class JPTestParams:
    def __init__(self, tb, fun_name: str, *parameters: Tuple[str, int]):
        self._tb = tb
        self._fun_name = fun_name
        self._wrapper: TestbookObjectReference

        self._parameters: Tuple[Tuple[str, int]] = parameters
        self._values: List[Dict[str, Any]] = []

    def __enter__(self):
        class_name = self._tb.random_id('Track')
        variable_name = self._tb.random_id('track')

        self._wrapper = self._tb.inject(f'''
            class {class_name}:
                def __init__(self, fun):
                    self._calls = []
                    self._results = []

                    def patch(*args, **kwargs):
                        self._calls.append((args, kwargs))
                        result = fun(*args, **kwargs)
                        self._results.append(result)

                        return result

                    self.fun = fun
                    self.patch = patch

                def extract_parameters(self, *parameters):
                    result = []
                    for args, kwargs in self._calls:
                        call_result = {{}}
                        result.append(call_result)

                        for name, pos in parameters:
                            if name in kwargs:
                                call_result[name] = kwargs[name]
                            elif pos < len(args):
                                call_result[name] = args[pos]

                    return result

            {variable_name} = {class_name}({self._fun_name})
            {self._fun_name} = {variable_name}.patch
        ''', variable_name)

        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self._tb.inject(f'''
            {self._fun_name} = {self._wrapper.name}.fun
        ''')

        self._values = self._wrapper.extract_parameters(*self._parameters)

    @property
    def name(self) -> str:
        return self._fun_name

    @property
    def parameter_names(self) -> List[str]:
        return list(map(lambda x: x[0], self._parameters))

    @property
    def calls(self) -> List[Dict[str, Any]]:
        return self._values

    @property
    def last_call(self) -> Dict[str, Any]:
        return self._values[-1]

    def values(self, parameter_name: str) -> List[Any]:
        result = []
        for call in self.calls:
            if parameter_name in call:
                result.append(call[parameter_name])

        return result

    def last_value(self, parameter_name: str) -> Any:
        return self.last_call[parameter_name]

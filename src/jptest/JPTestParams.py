from typing import List, Dict, Any, Tuple

from testbook.reference import TestbookObjectReference

from . import JPTestBook


class JPTestParams:
    """
    stores tracked parameters after __exit__ is called
    """
    def __init__(self, tb: JPTestBook, fun_name: str, *parameters: Tuple[str, int]):
        """
        :param tb:
        :param fun_name: function name to replace
        :param parameters: parameters to track as tuples (name, position)
        """
        self._tb = tb
        self._fun_name = fun_name
        self._wrapper: TestbookObjectReference

        self._parameters: Tuple[Tuple[str, int]] = parameters
        self._values: List[Dict[str, Any]] = []

    def __enter__(self):
        """
        replace function with wrapper

        :return: self
        """
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
        """
        extract parameters and replace wrapper with original function

        :param exc_type:
        :param exc_val:
        :param exc_tb:
        :return:
        """
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

    def __len__(self) -> int:
        return len(self.calls)

    def values(self, parameter_name: str) -> List[Any]:
        """
        returns all values for a specific parameter

        :param parameter_name: parameter name
        :return: list of parameter values
        """
        result = []
        for call in self.calls:
            if parameter_name in call:
                result.append(call[parameter_name])

        return result

    def last_value(self, parameter_name: str) -> Any:
        """
        returns the value for a specific parameter in the last call

        :param parameter_name: parameter name
        :return: parameter value
        """
        return self.last_call[parameter_name]

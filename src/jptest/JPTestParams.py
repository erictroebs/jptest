from typing import List, Dict, Any, Tuple


class JPTestParams:
    def __init__(self, name: str, parameters: List[Tuple[str, int]], values: List[Dict[str, Any]]):
        self._name = name
        self._parameters = parameters
        self._values = values

    def __str__(self):
        return f'{self._name}: {str(self._values)}'

    @property
    def name(self) -> str:
        return self._name

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

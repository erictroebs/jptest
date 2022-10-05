from typing import Tuple, List, Dict, Any, Optional

from . import Notebook


class NotebookFunctionCall:
    """
    stores tracked parameters and results
    """

    def __init__(self, nb: Notebook, fun_name: str,
                 call_parameters: Dict[str, Optional[Any]], return_value: Optional[Any]):
        """
        :param nb:
        :param fun_name: function name
        :param call_parameters: parameter name to parameter value mapping
        :param return_value: functions return value
        """
        self._nb = nb

        self._fun_name = fun_name
        self._parameters: Dict[str, Optional[Any]] = call_parameters
        self._return: Optional[Any] = return_value

    def __getattr__(self, key: str) -> Optional[Any]:
        return self._parameters[key]

    def __getitem__(self, key: str) -> Optional[Any]:
        return self._parameters[key]

    def __contains__(self, key: str) -> bool:
        return key in self._parameters

    @property
    def parameter_names(self) -> List[str]:
        """
        receive all captured parameter names

        :return: list of names
        """
        return list(self._parameters)

    @property
    def parameters(self) -> List[Tuple[str, Optional[Any]]]:
        """
        receive all captured parameter names and values

        :return: list of (name, value)
        """
        return list(self._parameters.items())

    @property
    def return_value(self) -> Optional[Any]:
        """
        receive return value

        :return: return value
        """
        return self._return

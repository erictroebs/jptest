import pytest

from jptest2 import PythonNotebook


@pytest.mark.asyncio
async def test_execute_function():
    # simple function
    # noinspection PyUnreachableCode
    def my_fun():
        fun_value = 1
        return fun_value + 1
        return fun_value + 10

    async with PythonNotebook('execute_code.ipynb') as nb:
        result = await nb.execute_fun(my_fun)
        assert result.output() == (
            [('text/plain', '2')],
            None,
            None,
            []
        )

        assert await nb.ref('fun_value').receive() == 1

    # more complex function
    # noinspection PyUnreachableCode
    def my_second_fun():
        fun_value = 1

        if fun_value == 2:
            fun_value = fun_value + 100
            return fun_value
            return fun_value + 10
        else:
            fun_value = fun_value + 1000
            return fun_value
            return fun_value + 10

    async with PythonNotebook('execute_code.ipynb') as nb:
        result = await nb.execute_fun(my_second_fun)
        assert result.output() == (
            [],
            None,
            None,
            []
        )

        assert await nb.ref('fun_value').receive() == 1001


@pytest.mark.asyncio
async def test_execute_inner_function():
    def outer_fun():
        def inner_fun():
            a = 1
            return a + 1

        inner_val = inner_fun()
        return inner_val + 2

    async with PythonNotebook('execute_code.ipynb') as nb:
        result = await nb.execute_fun(outer_fun)
        assert result.output() == (
            [('text/plain', '4')],
            None,
            None,
            []
        )

        assert await nb.ref('inner_val').receive() == 2


@pytest.mark.asyncio
async def test_inject_function():
    def my_fun():
        return 'abc', 1, 'def'

    async with PythonNotebook('execute_code.ipynb') as nb:
        nb_fun = await nb.inject_fun(my_fun)
        result = await nb_fun().receive()

        assert result == my_fun()


@pytest.mark.asyncio
async def test_inject_lambda_function():
    my_lambda = lambda x: x * x

    async with PythonNotebook('execute_code.ipynb') as nb:
        nb_fun = await nb.inject_fun(my_lambda)
        result = await nb_fun(12).receive()

        assert result == my_lambda(12)

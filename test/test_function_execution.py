import pytest

from jptest2.notebook import Notebook


@pytest.mark.asyncio
async def test_execute_function():
    # noinspection PyUnreachableCode
    def my_fun():
        fun_value = 1
        return fun_value + 1
        return fun_value + 10

    async with Notebook('execute_code.ipynb') as nb:
        result = await nb.execute_fun(my_fun)
        assert result.output() == (
            [('text/plain', str(my_fun()))],
            None,
            None,
            []
        )


@pytest.mark.asyncio
async def test_inject_function():
    def my_fun():
        return 'abc', 1, 'def'

    async with Notebook('execute_code.ipynb') as nb:
        nb_fun = await nb.inject_fun(my_fun)
        result_ref = await nb_fun()
        result = await result_ref.receive()

        assert result == my_fun()


@pytest.mark.asyncio
async def test_inject_lambda_function():
    my_lambda = lambda x: x * x

    async with Notebook('execute_code.ipynb') as nb:
        nb_fun = await nb.inject_fun(my_lambda)
        result_ref = await nb_fun(12)
        result = await result_ref.receive()

        assert result == my_lambda(12)

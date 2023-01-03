import pytest

from jptest2 import PythonNotebook


@pytest.mark.asyncio
async def test_replace_function():
    def local_fun(_, b):
        return b

    async with PythonNotebook('functions.ipynb') as nb:
        # execute cell with function definition
        await nb.execute_cells('definition')

        # replace function
        async with nb.replace_fun('nb_fun', local_fun):
            # compare results
            cells = await nb.execute_cells('execution')
            result, *_ = cells[0].output()

            assert any([val == '10' for _, val in result])

            await nb.execute_cells('store')
            result = await nb.ref('result').receive()
            assert result == 110

        # get results again after backup was restored
        cells = await nb.execute_cells('execution')
        result, *_ = cells[0].output()

        assert any([val == '5' for _, val in result])

        await nb.execute_cells('store')
        result = await nb.ref('result').receive()
        assert result == 105


@pytest.mark.asyncio
async def test_replace_module_function():
    def local_fun(*args, **kwargs):
        return 1, 2, 3

    async with PythonNotebook('functions.ipynb') as nb:
        # import module
        await nb.execute_code('''
            import math
        ''')

        # replace function in module
        async with nb.replace_fun('math.ceil', local_fun):
            # get function and receive result
            result = await nb.ref('math.ceil')().receive()
            assert result == (1, 2, 3)


@pytest.mark.asyncio
async def test_replace_class_function():
    def local_fun(*args, **kwargs):
        return 1, 2, 3

    async with PythonNotebook('functions.ipynb') as nb:
        # inject class
        await nb.execute_code('''
            class Test:
                def fun(self):
                    return 5
        ''')

        # replace function
        async with nb.replace_fun('Test.fun', local_fun):
            # create object and receive result
            await nb.execute_code('a = Test()')
            result = await nb.ref('a').fun().receive()

            assert result == (1, 2, 3)


@pytest.mark.asyncio
async def test_replace_object_function():
    def local_fun(*args, **kwargs):
        return 1, 2, 3

    async with PythonNotebook('functions.ipynb') as nb:
        # inject class
        await nb.execute_code('''
            class Test:
                def fun(self):
                    return 5
                    
            a = Test()
            b = Test()
        ''')

        # replace function
        async with nb.replace_fun('a.fun', local_fun):
            result_a = await nb.ref('a').fun().receive()
            assert result_a == (1, 2, 3)

            result_b = await nb.ref('b').fun().receive()
            assert result_b == 5

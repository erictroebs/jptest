from . import *


@JPTest('run')
async def run(nb: Notebook):
    # iterate over cells
    for cell in nb.cells:
        # find `jp:input` tag
        if 'jp:input' in cell.tags:
            # replace input function
            def replacement(arg):
                return arg

            # execute cell
            async with nb.replace_fun('input', replacement):
                await cell.execute()

        # execute cell normally
        else:
            await cell.execute()

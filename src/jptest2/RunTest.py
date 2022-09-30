from . import *


@JPTest('run')
async def run(nb: Notebook):
    # iterate over cells
    for cell in nb.cells:
        # find `jp:input` tag
        replace_input = None

        for tag in cell.tags:
            if tag.startswith('jp:input='):
                replace_input = tag[9:]

        # replace input function if necessary
        if replace_input is not None:
            def replacement(_):
                return replace_input

            async with nb.replace_fun('input', replacement):
                await cell.execute()

        # execute cell normally
        else:
            await cell.execute()

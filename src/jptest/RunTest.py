from . import *


@JPTest('run', max_score=0)
def run(tb: JPTestBook):
    # iterate over cells
    for cell in tb.cells():
        # find `jp:input` tag
        replace_input = None

        for tag in cell.tags:
            if tag.startswith('jp:input='):
                replace_input = tag[9:]

        # replace input function if necessary
        replace_name = None

        if replace_input is not None:
            replace_name = JPTestBook.random_id('input')
            tb.inject(f'''
                {replace_name} = input
                input = lambda _: '{replace_input}'
            ''')

        # execute cell
        cell.execute()

        # revert replacement
        if replace_input is not None:
            tb.inject(f'''
                input = {replace_name}
            ''')

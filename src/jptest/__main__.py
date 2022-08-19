import importlib.util
import json
import sys
from argparse import ArgumentParser
from typing import Dict, Tuple, List, Optional

from jptest import *

# configure argument parser
parser = ArgumentParser()
parser.add_argument('nb_file', help='notebook file (.ipynb) to load')
parser.add_argument('test_file', help='test file (.py) to load', nargs='?')
parser.add_argument('test_name', help='test to execute (all if None given)', nargs='?')
parser.add_argument('--json', action='store_true', help='print output as json (default)', default=True)
parser.add_argument('--md', action='store_true', help='print output as markdown')
parser.add_argument('--quiet', action='store_true', help='only print exceptions')
parser.add_argument('--verbose', '-v', action='store_true', help='print verbosely to stderr')

args = parser.parse_args()

# load classes from file
JPTest.NOTEBOOK = args.nb_file

if args.test_file is not None:
    spec = importlib.util.spec_from_file_location('testfile', args.test_file)
    foo = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = foo
    spec.loader.exec_module(foo)
else:
    # noinspection PyUnresolvedReferences
    from jptest.RunTest import *

# pre run functions
if args.verbose:
    print('pre run', file=sys.stderr)

for fun in JPPreRun.FN:
    fun()

# execute tests
achieved, total = 0.0, 0.0
tests: Dict[str, Tuple[str, float, float, List[str], Optional[Exception]]] = {}

for test, original_fun, wrapped_fun in JPTest.TESTS:
    test_name = original_fun.__name__

    if args.verbose:
        print(test_name, file=sys.stderr)

    # skip tests if required
    if args.test_name is not None and args.test_name != test_name:
        continue

    # execute test
    try:
        score, comments = wrapped_fun()

        achieved += score
        tests[test_name] = test.name, score, test.max_score, comments, None
    except Exception as e:
        tests[test_name] = test.name, 0, test.max_score, [str(e)], e

    total += test.max_score

# post run functions
if args.verbose:
    print('post run', file=sys.stderr)

for fun in JPPostRun.FN:
    fun()

# print output
if args.quiet:  # quiet
    for test_name, (_, score, max_score, _, e) in tests.items():
        if e is not None:
            raise e

        if score != max_score:
            raise AssertionError(f'test_name={test_name}, score={score}, max_score={max_score}')

elif args.md:  # md
    print(f'# Bewertung ({achieved} / {total})')
    print()

    for test_name, (name, score, max_score, comments, _) in tests.items():
        print(f'## {name} ({score} / {max_score})')
        for comment in comments:
            print(f'- {comment}')
        print()

else:  # json
    result = {
        'achievedScore': achieved,
        'totalScore': total,
        'tests': []
    }

    for test_name, (name, score, max_score, comments, _) in tests.items():
        result['tests'].append({
            'test': test_name,
            'name': name,
            'achievedScore': score,
            'totalScore': max_score,
            'comments': comments
        })

    print(json.dumps(result, indent=4))

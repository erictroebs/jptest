import argparse
import asyncio
import importlib.util
import json
import os
import sys
import traceback
from argparse import ArgumentParser
from asyncio import Semaphore

from jptest2 import JPTest, JPSetup, JPTeardown


async def test(args: argparse.Namespace):
    # override default timeout
    JPTest.DEFAULT_TIMEOUT = args.timeout

    # reset registered tests and other functions
    JPTest.TESTS = []
    JPSetup.FN = []
    JPTeardown.FN = []

    # load classes from file
    if args.test_file is not None:
        spec = importlib.util.spec_from_file_location('testfile', args.test_file)
        foo = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = foo
        spec.loader.exec_module(foo)
    else:
        # noinspection PyUnresolvedReferences
        import jptest2.RunTest

    # pre run functions
    if args.verbose:
        print('pre run', file=sys.stderr)

    if len(JPSetup.FN) > 0:
        await asyncio.gather(*[f() for f in JPSetup.FN])

    # filter and execute tests
    proc: Semaphore = Semaphore(args.tests)

    async def ensure_proc(async_fun):
        async with proc:
            return await async_fun

    tests = [t for t in JPTest.TESTS if args.test_name is None or args.test_name == t.test_name]
    results = await asyncio.gather(*[ensure_proc(t.execute(args.nb_file)) for t in tests])

    # post run functions
    if args.verbose:
        print('post run', file=sys.stderr)

    if len(JPTeardown.FN) > 0:
        await asyncio.gather(*[f() for f in JPTeardown.FN])

    # print output
    if args.quiet:  # quiet
        for test, (score, comments, e) in zip(tests, results):
            if e is not None:
                raise e

            if score != test.max_score:
                raise AssertionError(f'test_name={test.test_name}, score={score}, max_score={test.max_score}')

    elif args.md:  # md
        achieved = sum((score for score, _, _ in results))
        total = sum((test.max_score for test in tests))

        print(f'# Bewertung ({achieved} / {total})')
        print()

        for test, (score, comments, e) in zip(tests, results):
            print(f'## {test.name} ({score} / {test.max_score})')
            for comment in comments:
                print(f'- {comment}')
            print()

    else:  # json
        achieved = sum((score for score, _, _ in results))
        total = sum((test.max_score for test in tests))

        result = {
            'achievedScore': achieved,
            'totalScore': total,
            'tests': []
        }

        for test, (score, comments, e) in zip(tests, results):
            result['tests'].append({
                'test': test.test_name,
                'name': test.name,
                'achievedScore': score,
                'totalScore': test.max_score,
                'comments': comments
            })

        print(json.dumps(result, indent=4))


async def main():
    # configure argument parser
    parser = ArgumentParser()
    parser.add_argument('nb_file', help='notebook file (.ipynb) to load')
    parser.add_argument('test_file', help='test file (.py) to load', nargs='?')
    parser.add_argument('test_name', help='test to execute (all if None given)', nargs='?')
    parser.add_argument('--json', action='store_true', help='print output as json (default)', default=True)
    parser.add_argument('--tests', type=int, help='number of tests to process concurrently', default=1000)
    parser.add_argument('--md', action='store_true', help='print output as markdown')
    parser.add_argument('--timeout', type=int, help='override default timeout in seconds (default 120s)', default=120)
    parser.add_argument('--quiet', action='store_true', help='only print exceptions')
    parser.add_argument('--verbose', '-v', action='store_true', help='print verbosely to stderr')
    parser.add_argument('--live', action='store_true', help='run infinitely and watch for changes')

    args = parser.parse_args()

    # default mode
    if not args.live:
        await test(args)

    # live mode
    else:
        from watchfiles import awatch

        os.system('clear')
        await test(args)

        async for changes in awatch(args.nb_file, args.test_file):
            os.system('clear')
            try:
                await test(args)
            except Exception as e:
                traceback.print_exception(e)


if __name__ == '__main__':
    asyncio.run(main())

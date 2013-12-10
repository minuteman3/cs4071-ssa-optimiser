#!/usr/bin/env python
from __future__ import print_function
from argparse import ArgumentParser, FileType
from sys import stderr
import json


def main():
    parser = ArgumentParser()
    parser.add_argument('input',
                        nargs='?',
                        type=FileType('r'),
                        default='-')

    args = parser.parse_args()

    try:
        infile = json.loads(args.input.read())
    except ValueError:
        print("ERROR: Invalid JSON passed as input", file=stderr)


if __name__ == "__main__":
    main()

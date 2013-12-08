#!/usr/bin/env python
import argparse
import json
from sys import stderr


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('input',
                        nargs='?',
                        type=argparse.FileType('r'),
                        default='-')

    args = parser.parse_args()

    try:
        infile = json.loads(args.input.read())
    except ValueError:
        print("ERROR: Invalid JSON passed as input", file=stderr)


if __name__ == "__main__":
    main()

import sys

from sbc import data


def main(argv):
    cmd = argv[0] if argv else "help"
    if cmd == "fetch":
        data.fetch_treasury("par", range(1990, 2027))
        data.fetch_treasury("real", range(2003, 2027))
        data.fetch_yahoo()
        data.write_snapshot()
    else:
        print("usage: python -m sbc fetch")


if __name__ == "__main__":
    main(sys.argv[1:])

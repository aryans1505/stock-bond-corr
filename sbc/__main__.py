import sys

from sbc import data


def main(argv):
    cmd = argv[0] if argv else "help"
    if cmd == "fetch":
        data.fetch_treasury("par", range(1990, 2027))
        data.fetch_treasury("real", range(2003, 2027))
        data.fetch_yahoo()
        data.write_snapshot()
    elif cmd in ("report", "reproduce"):
        # reproduce = every number and figure in the README from the data/raw snapshot
        from sbc import report
        report.run()
    else:
        print("usage: python -m sbc fetch|report|reproduce")


if __name__ == "__main__":
    main(sys.argv[1:])

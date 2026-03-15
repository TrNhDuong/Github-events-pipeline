def gold_layer_execution(year: int, month: int, day: int):
    pass

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--year",  type=int)
    parser.add_argument("--month", type=int)
    parser.add_argument("--day",   type=int)
    args = parser.parse_args()

    gold_layer_execution(args.year, args.month, args.day)
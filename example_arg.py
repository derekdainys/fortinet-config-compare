import argparse
from config_compare.compare import config_compare

def main():
    parser = argparse.ArgumentParser(description="A program that will show a diff between two fortinet configurations")
    parser.add_argument("-r","--running", help="name of the file for running config")
    parser.add_argument("-c", "--candidate", help="name of the file for the candidate config")

    args = parser.parse_args()
    diff_config = config_compare(running=args.running, candidate=args.candidate, indent=0)
    revert_config = config_compare(running=args.candidate, candidate=args.running, indent=0)
    print(f"Running -> Candidate")
    print("*" * 50)
    print(diff_config)

    print(f"Revert: Candidate -> Running")
    print("*" * 50)
    print(revert_config)


if __name__ == "__main__":
    main()
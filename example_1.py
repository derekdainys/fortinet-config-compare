from config_compare.compare import config_compare

def main():
    print(config_compare(running="configs/running.conf", candidate="configs/candidate.conf", indent=3))

if __name__ == "__main__":
    main()
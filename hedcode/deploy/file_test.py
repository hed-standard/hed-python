import sys


def main(filepath):
    with open(filepath) as f:
        lines = f.readlines()
    print(f"The contents:\n {str(lines)}")


if __name__ == '__main__':
    file_path = '/data/requirements.txt'
    sys.exit(main(file_path))

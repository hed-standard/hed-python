import os
import subprocess


if __name__ == '__main__':
    # try:
    #     proc = subprocess.Popen(['docker', 'version'], stdout=subprocess.PIPE,
    #                             stderr=subprocess.PIPE, bufsize=1)
    #     print(proc.communicate())
    # except OSError as ex:
    #     print(f"to here{ex}")

    try:
        proc = subprocess.Popen(['docker', 'version'], stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE, bufsize=1)

        output = proc.stdout.readlines()
        print(output)
        print(f"\n\nNow print by line (output contains {len(output)} lines):")
        for out in output:
            print(f"{str(out, 'utf-8')}")

    except OSError as ex:
        print(f"to here{ex}")
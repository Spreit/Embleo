import os
import subprocess

requirenments_path = "./requirenments.txt"

# Call cmd to install everything
commands = ["pip", "install", "--requirement", requirenments_path]
subprocess.call(commands)

print("")
print("Installed required Python Modules")
print("Press any button to close")
input()
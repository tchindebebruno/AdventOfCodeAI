import sys
lines = sys.stdin.read().splitlines()
total = 0
for line in lines:
    max_joltage = 0
    for i in range(len(line)):
        for j in range(i+1, len(line)):
            val = int(line[i] + line[j])
            if val > max_joltage:
                max_joltage = val
    total += max_joltage
print(total)
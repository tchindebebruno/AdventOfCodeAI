import sys
lines = [line.strip() for line in sys.stdin if line.strip()]
pos = 50
count = 0
for line in lines:
    d, n = line[0], int(line[1:])
    if d == 'L':
        pos = (pos - n) % 100
    else:
        pos = (pos + n) % 100
    if pos == 0:
        count += 1
print(count)
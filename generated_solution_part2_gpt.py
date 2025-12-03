import sys
lines = sys.stdin.read().splitlines()
total = 0
for line in lines:
    digits = list(line.strip())
    n = len(digits)
    best = ''.join(sorted(digits, reverse=True)[:12])
    # Problem: must preserve input order, not rearrange digits
    # So, pick all possible sets of 12 indices (positions), and choose the one with the lex greatest resulting string
    # For short lines, pad left with '0's
    from itertools import combinations
    indices = range(n)
    maxval = ''
    for combo in combinations(indices, 12):
        out = ''.join(digits[i] for i in combo)
        if out > maxval:
            maxval = out
    total += int(maxval)
print(total)
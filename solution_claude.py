import sys

def max_joltage_from_bank(bank):
    digits = [int(d) for d in bank.strip()]
    n = len(digits)
    max_val = 0
    
    for i in range(n):
        for j in range(i+1, n):
            val = digits[i] * 10 + digits[j]
            max_val = max(max_val, val)
    
    return max_val

input_data = sys.stdin.read().strip()
banks = input_data.split('\n')

total = 0
for bank in banks:
    if bank:
        total += max_joltage_from_bank(bank)

print(total)
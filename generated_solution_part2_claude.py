import sys

def solve():
    lines = sys.stdin.read().strip().split('\n')
    total = 0
    
    for line in lines:
        digits = [int(d) for d in line]
        n = len(digits)
        
        # We need to select exactly 12 digits to maximize the resulting number
        # To maximize a 12-digit number, we want the largest possible digits
        # in the leftmost positions
        
        # Sort digits with their original indices to track positions
        indexed_digits = [(digits[i], i) for i in range(n)]
        
        # We need to select 12 digits that maintain their relative order
        # and form the largest possible number
        
        # Greedy approach: for each position in the result (left to right),
        # choose the largest available digit that still allows us to
        # select enough remaining digits
        
        selected = []
        remaining_positions = list(range(n))
        
        for pos in range(12):
            # How many more digits do we need after this one?
            remaining_needed = 12 - pos - 1
            
            # Find the largest digit we can choose that still leaves
            # enough positions for the remaining digits
            best_digit = -1
            best_idx = -1
            
            for i, orig_pos in enumerate(remaining_positions):
                # Can we still select remaining_needed digits after this position?
                remaining_after = len(remaining_positions) - i - 1
                if remaining_after >= remaining_needed:
                    if digits[orig_pos] > best_digit:
                        best_digit = digits[orig_pos]
                        best_idx = i
            
            # Select this digit
            selected.append(best_digit)
            # Remove all positions up to and including the selected one
            remaining_positions = remaining_positions[best_idx + 1:]
        
        # Convert selected digits to number
        bank_joltage = int(''.join(map(str, selected)))
        total += bank_joltage
    
    print(total)

solve()
import sys

input_lines = [line.strip() for line in sys.stdin if line.strip()]

position = 50
result = 0
DIAL_SIZE = 100

for line in input_lines:
    direction = line[0]
    dist = int(line[1:])

    prev_pos = position

    if direction == "L":
        # distance to zero going left ("down")
        steps_to_zero = (prev_pos - 0) % DIAL_SIZE
        if dist >= steps_to_zero:
            result += 1 + ((dist-steps_to_zero-1)//DIAL_SIZE)
        else:
            # may pass multiple zeros with e.g. L150, starting at 90
            result += (dist // DIAL_SIZE)
        position = (prev_pos - dist) % DIAL_SIZE
    else:
        # direction == R
        steps_to_zero = (0 - prev_pos) % DIAL_SIZE
        if dist >= steps_to_zero:
            result += 1 + ((dist-steps_to_zero-1)//DIAL_SIZE)
        else:
            result += (dist // DIAL_SIZE)
        position = (prev_pos + dist) % DIAL_SIZE

print(result)
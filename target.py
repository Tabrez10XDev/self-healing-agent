def calculate_average(numbers):
    # Bug 1: integer division instead of float
    # Bug 2: empty list returns 0 but as wrong type
    if not numbers:
        return 0        # returns int, should be float 0.0
    total = 0
    for n in numbers:
        total += n
    return total // len(numbers)   # integer division loses decimals


def reverse_string(s):
    # Bug: skips spaces during reversal
    result = ""
    for char in s:
        if char != " ":            # wrongly filters spaces
            result = char + result
    return result


def count_vowels(s):
    # Bug: misses 'u' and 'U' from vowel check
    vowels = "aeiAEI"             # incomplete vowel list
    count = 0
    for char in s:
        if char in vowels:
            count += 1
    return count
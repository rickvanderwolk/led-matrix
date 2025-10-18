import os
import json
import time
import random
import board
import neopixel

CONFIG_PATH = os.environ.get("LEDMATRIX_CONFIG", "config.json")
with open(CONFIG_PATH) as f:
    config = json.load(f)

LED_COUNT = 64
PIN = board.D18
BRIGHTNESS = config.get("brightness", 0.2)
SLEEP_BETWEEN_CHANGES = 0.1
SLEEP_BETWEEN_ALGORITHMS = 2

matrix = neopixel.NeoPixel(PIN, LED_COUNT, brightness=BRIGHTNESS, auto_write=False)

def get_matrix_index(i):
    return i

def update_leds(array, changed_indices=None):
    updated = False
    for i in range(LED_COUNT):
        idx = get_matrix_index(i)
        if changed_indices and i in changed_indices:
            new_color = (255, 255, 255)
        elif array[i] == i:
            new_color = (0, 255, 0)
        else:
            new_color = (255, 0, 0)

        if matrix[idx] != new_color:
            matrix[idx] = new_color
            updated = True

    if updated:
        matrix.show()

def shuffled_array():
    values = list(range(LED_COUNT))
    random.shuffle(values)
    return values

def bubble_sort(values):
    for i in range(LED_COUNT):
        for j in range(0, LED_COUNT - i - 1):
            if values[j] > values[j + 1]:
                values[j], values[j + 1] = values[j + 1], values[j]
                update_leds(values, [j, j + 1])
                time.sleep(SLEEP_BETWEEN_CHANGES)

def insertion_sort(values):
    for i in range(1, LED_COUNT):
        key = values[i]
        j = i - 1
        while j >= 0 and values[j] > key:
            values[j + 1] = values[j]
            update_leds(values, [j, j + 1])
            time.sleep(SLEEP_BETWEEN_CHANGES)
            j -= 1
        values[j + 1] = key
        update_leds(values, [j + 1])
        time.sleep(SLEEP_BETWEEN_CHANGES)

def selection_sort(values):
    for i in range(LED_COUNT):
        min_idx = i
        for j in range(i + 1, LED_COUNT):
            if values[j] < values[min_idx]:
                min_idx = j
        values[i], values[min_idx] = values[min_idx], values[i]
        update_leds(values, [i, min_idx])
        time.sleep(SLEEP_BETWEEN_CHANGES)

def quick_sort(values, start, end):
    if start < end:
        pivot = partition(values, start, end)
        update_leds(values)
        time.sleep(SLEEP_BETWEEN_CHANGES)
        quick_sort(values, start, pivot - 1)
        quick_sort(values, pivot + 1, end)

def partition(values, start, end):
    pivot = values[end]
    i = start - 1
    for j in range(start, end):
        if values[j] < pivot:
            i += 1
            values[i], values[j] = values[j], values[i]
            update_leds(values, [i, j])
            time.sleep(SLEEP_BETWEEN_CHANGES)
    values[i + 1], values[end] = values[end], values[i + 1]
    update_leds(values, [i + 1, end])
    time.sleep(SLEEP_BETWEEN_CHANGES)
    return i + 1

def merge_sort(values, start, end):
    if end - start > 1:
        mid = (start + end) // 2
        merge_sort(values, start, mid)
        merge_sort(values, mid, end)
        merge(values, start, mid, end)

def merge(values, start, mid, end):
    left = values[start:mid]
    right = values[mid:end]
    i = j = 0
    k = start
    while i < len(left) and j < len(right):
        if left[i] <= right[j]:
            values[k] = left[i]
            source_idx = start + i
            i += 1
        else:
            values[k] = right[j]
            source_idx = mid + j
            j += 1
        update_leds(values, [k, source_idx])
        time.sleep(SLEEP_BETWEEN_CHANGES)
        k += 1
    while i < len(left):
        values[k] = left[i]
        source_idx = start + i
        update_leds(values, [k, source_idx])
        time.sleep(SLEEP_BETWEEN_CHANGES)
        i += 1
        k += 1
    while j < len(right):
        values[k] = right[j]
        source_idx = mid + j
        update_leds(values, [k, source_idx])
        time.sleep(SLEEP_BETWEEN_CHANGES)
        j += 1
        k += 1

def pancake_sort(values):
    def flip(n):
        start = 0
        while start < n:
            values[start], values[n] = values[n], values[start]
            update_leds(values, [start, n])
            time.sleep(SLEEP_BETWEEN_CHANGES)
            start += 1
            n -= 1
    for curr_size in range(LED_COUNT, 1, -1):
        max_idx = values.index(max(values[:curr_size]))
        if max_idx != curr_size - 1:
            flip(max_idx)
            flip(curr_size - 1)

def gnome_sort(values):
    index = 0
    while index < LED_COUNT:
        if index == 0 or values[index] >= values[index - 1]:
            index += 1
        else:
            values[index], values[index - 1] = values[index - 1], values[index]
            update_leds(values, [index, index - 1])
            time.sleep(SLEEP_BETWEEN_CHANGES)
            index -= 1

def comb_sort(values):
    gap = LED_COUNT
    shrink = 1.3
    sorted = False
    while not sorted:
        gap = int(gap // shrink)
        if gap <= 1:
            gap = 1
            sorted = True
        i = 0
        while i + gap < LED_COUNT:
            if values[i] > values[i + gap]:
                values[i], values[i + gap] = values[i + gap], values[i]
                update_leds(values, [i, i + gap])
                time.sleep(SLEEP_BETWEEN_CHANGES)
                sorted = False
            i += 1

def cocktail_shaker_sort(values):
    swapped = True
    start = 0
    end = LED_COUNT - 1
    while swapped:
        swapped = False
        for i in range(start, end):
            if values[i] > values[i + 1]:
                values[i], values[i + 1] = values[i + 1], values[i]
                update_leds(values, [i, i + 1])
                time.sleep(SLEEP_BETWEEN_CHANGES)
                swapped = True
        if not swapped:
            break
        swapped = False
        end -= 1
        for i in range(end - 1, start - 1, -1):
            if values[i] > values[i + 1]:
                values[i], values[i + 1] = values[i + 1], values[i]
                update_leds(values, [i, i + 1])
                time.sleep(SLEEP_BETWEEN_CHANGES)
                swapped = True
        start += 1

def shell_sort(values):
    gap = LED_COUNT // 2
    while gap > 0:
        for i in range(gap, LED_COUNT):
            temp = values[i]
            j = i
            while j >= gap and values[j - gap] > temp:
                values[j] = values[j - gap]
                update_leds(values, [j, j - gap])
                time.sleep(SLEEP_BETWEEN_CHANGES)
                j -= gap
            values[j] = temp
        gap //= 2

def heap_sort(values):
    def heapify(n, i):
        largest = i
        l = 2 * i + 1
        r = 2 * i + 2
        if l < n and values[l] > values[largest]:
            largest = l
        if r < n and values[r] > values[largest]:
            largest = r
        if largest != i:
            values[i], values[largest] = values[largest], values[i]
            update_leds(values, [i, largest])
            time.sleep(SLEEP_BETWEEN_CHANGES)
            heapify(n, largest)

    n = LED_COUNT
    for i in range(n // 2 - 1, -1, -1):
        heapify(n, i)
    for i in range(n - 1, 0, -1):
        values[i], values[0] = values[0], values[i]
        update_leds(values, [i, 0])
        time.sleep(SLEEP_BETWEEN_CHANGES)
        heapify(i, 0)

def stooge_sort(values, i, j):
    if values[j] < values[i]:
        values[i], values[j] = values[j], values[i]
        update_leds(values, [i, j])
        time.sleep(SLEEP_BETWEEN_CHANGES)
    if j - i + 1 > 2:
        t = (j - i + 1) // 3
        stooge_sort(values, i, j - t)
        stooge_sort(values, i + t, j)
        stooge_sort(values, i, j - t)

def radix_sort(values):
    max_val = max(values)
    exp = 1
    while max_val // exp > 0:
        counting_sort(values, exp)
        exp *= 10

def counting_sort(values, exp):
    n = LED_COUNT
    output = [0] * n
    count = [0] * 10

    # Create a copy to track original positions
    original_values = values.copy()

    for i in range(n):
        index = (values[i] // exp) % 10
        count[index] += 1
    for i in range(1, 10):
        count[i] += count[i - 1]
    i = n - 1
    while i >= 0:
        index = (values[i] // exp) % 10
        dest_pos = count[index] - 1
        output[dest_pos] = values[i]
        count[index] -= 1
        i -= 1

    # Copy back and visualize the movement
    for i in range(n):
        if values[i] != output[i]:
            # Find where this output value came from in the original array
            source_idx = original_values.index(output[i])
            values[i] = output[i]
            update_leds(values, [i, source_idx])
            time.sleep(SLEEP_BETWEEN_CHANGES)
            # Mark as used to handle duplicates
            original_values[source_idx] = -1
        else:
            values[i] = output[i]
            update_leds(values, [i])
            time.sleep(SLEEP_BETWEEN_CHANGES)

def flash_sort(values):
    n = len(values)
    m = int(0.43 * n)
    min_val = min(values)
    max_val = max(values)
    if min_val == max_val:
        return
    l = [0] * m
    for v in values:
        k = int((m - 1) * (v - min_val) / (max_val - min_val))
        l[k] += 1
    for i in range(1, m):
        l[i] += l[i - 1]
    move = 0
    j = 0
    k = m - 1
    while move < n:
        while j > l[k] - 1:
            j += 1
            k = int((m - 1) * (values[j] - min_val) / (max_val - min_val))
        flash = values[j]
        while j != l[k]:
            k = int((m - 1) * (flash - min_val) / (max_val - min_val))
            hold = values[l[k] - 1]
            values[l[k] - 1] = flash
            flash = hold
            l[k] -= 1
            update_leds(values)
            time.sleep(SLEEP_BETWEEN_CHANGES)
            move += 1
    insertion_sort(values)

def odd_even_sort(values):
    sorted = False
    while not sorted:
        sorted = True
        for i in range(1, LED_COUNT - 1, 2):
            if values[i] > values[i + 1]:
                values[i], values[i + 1] = values[i + 1], values[i]
                update_leds(values, [i, i + 1])
                time.sleep(SLEEP_BETWEEN_CHANGES)
                sorted = False
        for i in range(0, LED_COUNT - 1, 2):
            if values[i] > values[i + 1]:
                values[i], values[i + 1] = values[i + 1], values[i]
                update_leds(values, [i, i + 1])
                time.sleep(SLEEP_BETWEEN_CHANGES)
                sorted = False

def cycle_sort(values):
    for cycle_start in range(LED_COUNT - 1):
        item = values[cycle_start]
        pos = cycle_start
        for i in range(cycle_start + 1, LED_COUNT):
            if values[i] < item:
                pos += 1
        if pos == cycle_start:
            continue
        while item == values[pos]:
            pos += 1
        values[pos], item = item, values[pos]
        update_leds(values, [cycle_start, pos])
        time.sleep(SLEEP_BETWEEN_CHANGES)
        while pos != cycle_start:
            pos = cycle_start
            for i in range(cycle_start + 1, LED_COUNT):
                if values[i] < item:
                    pos += 1
            while item == values[pos]:
                pos += 1
            values[pos], item = item, values[pos]
            update_leds(values, [cycle_start, pos])
            time.sleep(SLEEP_BETWEEN_CHANGES)

def slow_sort(values, i, j):
    if i >= j:
        return
    m = (i + j) // 2
    slow_sort(values, i, m)
    slow_sort(values, m + 1, j)
    if values[j] < values[m]:
        values[j], values[m] = values[m], values[j]
        update_leds(values, [j, m])
        time.sleep(SLEEP_BETWEEN_CHANGES)
    slow_sort(values, i, j - 1)

def odd_even_transposition_sort(values):
    sorted = False
    while not sorted:
        sorted = True
        for i in range(1, LED_COUNT - 1, 2):
            if values[i] > values[i + 1]:
                values[i], values[i + 1] = values[i + 1], values[i]
                update_leds(values, [i, i + 1])
                time.sleep(SLEEP_BETWEEN_CHANGES)
                sorted = False
        for i in range(0, LED_COUNT - 1, 2):
            if values[i] > values[i + 1]:
                values[i], values[i + 1] = values[i + 1], values[i]
                update_leds(values, [i, i + 1])
                time.sleep(SLEEP_BETWEEN_CHANGES)
                sorted = False

def bogosort(values):
    def is_sorted(arr):
        return all(arr[i] <= arr[i + 1] for i in range(len(arr) - 1))
    while not is_sorted(values):
        old = values.copy()
        random.shuffle(values)
        changed = [i for i in range(LED_COUNT) if values[i] != old[i]]
        update_leds(values, changed)
        time.sleep(SLEEP_BETWEEN_CHANGES)

def run_sort(name, func):
    values = shuffled_array()
    update_leds(values)
    time.sleep(1)
    if name == "quick":
        func(values, 0, LED_COUNT - 1)
    elif name == "merge":
        func(values, 0, LED_COUNT)
    elif name == "stooge":
        func(values, 0, LED_COUNT - 1)
    elif name == "slow":
        func(values, 0, LED_COUNT - 1)
    else:
        func(values)
    update_leds(values)
    time.sleep(SLEEP_BETWEEN_ALGORITHMS)

algorithms = [
    ("bubble", bubble_sort),
    ("insertion", insertion_sort),
    ("selection", selection_sort),
    ("quick", quick_sort),
    ("merge", merge_sort),
    ("pancake", pancake_sort),
    ("gnome", gnome_sort),
    ("comb", comb_sort),
    ("cocktail", cocktail_shaker_sort),
    ("shell", shell_sort),
    ("heap", heap_sort),
    ("stooge", stooge_sort),
    ("radix", radix_sort),
    ("flash", flash_sort),
    ("odd_even", odd_even_sort),
    ("cycle", cycle_sort),
    ("slow", slow_sort),
    ("odd_even_trans", odd_even_transposition_sort),
    # ("bogosort", bogosort)
]

while True:
    for name, func in algorithms:
        run_sort(name, func)

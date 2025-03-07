def match(score, array):
    closest_index = 0
    for idx, elem in enumerate(array):
        if elem <= score:
            closest_index = idx + 1
        else:
            break
    return closest_index

def choose(index, *args):
    return args[index - 1] if 0 < index <= len(args) else 0

class Benchmark:

    def __init__(self, thresholds, energy_thresholds):
        self.thresholds = thresholds
        self.energy_thresholds = energy_thresholds

    def get_energy(self, score, hash_):
        t1, t2, t3, t4 = self.thresholds[hash_]
        e1, e2, e3, e4 = self.energy_thresholds

        match_array = [0, t1 - (t2 - t1), t1, t2, t3, t4]
        match_idx = match(score, match_array)
        if match_idx == 0:
            return 0

        base = choose(match_idx, 0, self.energy_thresholds[0] - 100, e1, e2, e3, e4)
        adjustment = score - choose(match_idx, 0, t1 - (t2 - t1), t1, t2, t3, t4)
        denominator = choose(match_idx, t1 - (t2 - t1), t2 - t1, t2 - t1, t3 - t2, t4 - t3, t4 - t3)
        factor = choose(match_idx, self.energy_thresholds[0] - 100, e1 - self.energy_thresholds[0] - 100, e2 - e1, e3 - e2, e4 - e3, e4 - e3)

        if denominator == 0:
            return 0
        
        result = base + (adjustment / denominator) * factor
        return result
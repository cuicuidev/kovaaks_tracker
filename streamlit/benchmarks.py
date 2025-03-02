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

class IntermediateVT5:
    VOLTAIC_S5_INTERMEDIATE = {
        "830238e82c367ad2ba40df1da9968131" : (760, 840, 910, 970), # PASU
        "86f9526f57828ad981f6c93b35811f94" : (600, 690, 780, 860), # POPCORN
        "37975ba4bbbd5f9c593e7dbd72794baa" : (1120, 1220, 1310, 1390), # 1W3TS
        "5c7668cf07b550bb2b7956f5709cf84e" : (1310, 1400, 1490, 1570), # WW5T
        "ec8acdea37fa767767d705e389db1463" : (940, 1040, 1140, 1230), # FROGTAGON
        "47124ba125c1807fc7deb011c2f545a7" : (610, 690, 770, 860), # FLOATING HEADS
        "b11e423dba738357ce774a01422e9d91" : (2375, 2750, 3100, 3375), # PGT
        "ff38084d283c4e285150faee9c6b2832" : (2850, 3200, 3500, 3725), # SNAKE TRACK
        "c4c11bf8a727b6e6c836138535bd0879" : (2175, 2550, 2800, 3175), # AETHER
        "489b27e681807e0212eef50241bb0769" : (2525, 2850, 3100, 3350), # GROUND
        "865d54422da5368dc290d1bbc2b9b566" : (2775, 3200, 3550, 3875), # RAW CONTROL
        "a5fa9fbc3d55851b11534c60b85a9247" : (2750, 3175, 3525, 3825), # CONTROLSPHERE
        "dfb397975f6fcec5bd2ebf3cd0b7a66a" : (1110, 1170, 1230, 1270), # DOT TS
        "03d6156260b1b2b7893b746354b889c2" : (900, 960, 1020, 1080), # EDDIE TS
        "ff777f42a21d6ddcf8791caf2821a2bd" : (390, 430, 460, 490), # DRIFT TS
        "138c732d61151697949af4a3f51311fa" : (470, 510, 540, 570), # FLY TS
        "e3b4fdab121562a8d4c8c2ac426c890c" : (430, 460, 490, 520), # CONTROL TS
        "7cd5eee66632ebec0c33218d218ebf95" : (450, 500, 540, 590), # PENTA BOUNCE
    }

    def get_energy(self, score, hash_):
        t1, t2, t3, t4 = self.VOLTAIC_S5_INTERMEDIATE[hash_]
        e1, e2, e3, e4 = 500, 600, 700, 800

        match_array = [0, t1 - (t2 - t1), t1, t2, t3, t4]
        match_idx = match(score, match_array)
        if match_idx == 0:
            return 0

        base = choose(match_idx, 0, 400, e1, e2, e3, e4)
        adjustment = score - choose(match_idx, 0, t1 - (t2 - t1), t1, t2, t3, t4)
        denominator = choose(match_idx, t1 - (t2 - t1), t2 - t1, t2 - t1, t3 - t2, t4 - t3, t4 - t3)
        factor = choose(match_idx, 400, e1 - 400, e2 - e1, e3 - e2, e4 - e3, e4 - e3)

        if denominator == 0:
            return 0
        
        result = base + (adjustment / denominator) * factor
        return result
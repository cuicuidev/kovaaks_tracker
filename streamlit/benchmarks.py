from enum import Enum
from abc import ABC, abstractmethod
from typing import Union, Dict, Tuple, Optional

Number = Union[int, float]

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

class SkillMixin(ABC):
    _max_energy: int = 0

    def energy(self: "SkillMixin", score_a: Number, score_b: Number) -> int:
        energy_a = self._energy(score_a, self.scenario_a.value.thresholds)
        energy_b = self._energy(score_b, self.scenario_b.value.thresholds)
        return int(min(self._max_energy, max(energy_a, energy_b)))

    @abstractmethod
    def _energy(self: "SkillMixin", score: Number, thresholds: Tuple[int, int, int, int]) -> int:
        pass

    @property
    @abstractmethod
    def _ranks(self: "SkillMixin") -> Dict[str, int]:
        pass

class NoviceMixin(SkillMixin):
    _previous_energy: int = 0
    _max_energy: int = 500

    def _energy(self: "NoviceMixin", score: Number, thresholds: Tuple[int, int, int, int]) -> int:
        """
        = ELEGIR(COINCIDIR(E3, {0, L3:O3}), 0, L$2, M$2, N$2, O$2) # BASE

        + (E3 - ELEGIR(COINCIDIR(E3, {0, L3:O3}), 0, L3, M3, N3, O3)) # ADJUSTMENT

        / ELEGIR(COINCIDIR(E3, {0, L3:O3}), L3, M3-L3, N3-M3, O3-N3, O3-N3) # DENOMINATOR

        * ELEGIR(COINCIDIR(E3, {0, L3:O3}), L$2, M$2-L$2, N$2-M$2, O$2-N$2, O$2-N$2) # FACTOR
        """
        t1, t2, t3, t4 = thresholds # Row 3 on the spreadsheet
        e1, e2, e3, e4 = self._ranks.values() # Row 2 on the spreadsheet

        match_array = [0, t1, t2, t3, t4]
        match_idx = match(score, match_array)
        if match_idx == 0:
            return 0

        base = choose(match_idx, self._previous_energy, e1, e2, e3, e4)
        adjustment = score - choose(match_idx, 0, t1, t2, t3, t4)
        denominator = choose(match_idx, t1, t2 - t1, t3 - t2, t4 - t3, t4 - t3)
        factor = choose(match_idx, e1, e2 - e1, e3 - e2, e4 - e3, e4 - e3)

        if denominator == 0:
            return 0
        
        result = base + (adjustment / denominator) * factor
        return result

    @property
    def _ranks(self: "NoviceMixin") -> Dict[str, int]:
        return {"Iron" : 100, "Bronze" : 200, "Silver" : 300, "Gold" : 400}

class IntermediateMixin(SkillMixin):
    _previous_energy: int = 400
    _max_energy: int = 900

    def _energy(self: "IntermediateMixin", score: Number, thresholds: Tuple[int, int, int, int]) -> int:
        """
        = ELEGIR(COINCIDIR(E3, {0, L3-(M3-L3), L3:O3}), 0, Novice!O$2, L$2, M$2, N$2, O$2)

        + (E3 - ELEGIR(COINCIDIR(E3, {0, L3-(M3-L3), L3:O3}), 0, L3-(M3-L3), L3, M3, N3, O3))

        / ELEGIR(COINCIDIR(E3, {0, L3-(M3-L3), L3:O3}), L3-(M3-L3), M3-L3, M3-L3, N3-M3, O3-N3, O3-N3)

        * ELEGIR(COINCIDIR(E3, {0, L3-(M3-L3), L3:O3}), Novice!O$2, L$2-Novice!O$2, M$2-L$2, N$2-M$2, O$2-N$2, O$2-N$2)
        """
        t1, t2, t3, t4 = thresholds
        e1, e2, e3, e4 = self._ranks.values()

        match_array = [0, t1 - (t2 - t1), t1, t2, t3, t4]
        match_idx = match(score, match_array)
        if match_idx == 0:
            return 0

        base = choose(match_idx, 0, self._previous_energy, e1, e2, e3, e4)
        adjustment = score - choose(match_idx, 0, t1 - (t2 - t1), t1, t2, t3, t4)
        denominator = choose(match_idx, t1 - (t2 - t1), t2 - t1, t2 - t1, t3 - t2, t4 - t3, t4 - t3)
        factor = choose(match_idx, self._previous_energy, e1 - self._previous_energy, e2 - e1, e3 - e2, e4 - e3, e4 - e3)

        if denominator == 0:
            return 0
        
        result = base + (adjustment / denominator) * factor
        return result

    @property
    def _ranks(self: "IntermediateMixin") -> Dict[str, int]:
        return {"Platinum" : 500, "Diamond" : 600, "Jade" : 700, "Master" : 800}

class AdvancedMixin(SkillMixin):
    _previous_energy: int = 800
    _max_energy: int = 1200

    def _energy(self: "AdvancedMixin", score: Number, thresholds: Tuple[int, int, int, int]) -> int:
        """
        = ELEGIR(COINCIDIR(E3, {0, L3-(M3-L3), L3:O3}), 0, Intermediate!O$2, L$2, M$2, N$2, O$2)

        + (E3 - ELEGIR(COINCIDIR(E3, {0, L3-(M3-L3), L3:O3}), 0, L3-(M3-L3), L3, M3, N3, O3))

        / ELEGIR(COINCIDIR(E3, {0, L3-(M3-L3), L3:O3}), L3-(M3-L3), M3-L3, M3-L3, N3-M3, O3-N3, O3-N3)

        * ELEGIR(COINCIDIR(E3, {0, L3-(M3-L3), L3:O3}), Intermediate!O$2, L$2-Intermediate!O$2, M$2-L$2, N$2-M$2, O$2-N$2, O$2-N$2)
        """
        t1, t2, t3, t4 = thresholds
        e1, e2, e3, e4 = self._ranks.values()

        match_array = [0, t1 - (t2 - t1), t1, t2, t3, t4]
        match_idx = match(score, match_array)
        if match_idx == 0:
            return 0

        base = choose(match_idx, 0, self._previous_energy, e1, e2, e3, e4)
        adjustment = score - choose(match_idx, 0, t1 - (t2 - t1), t1, t2, t3, t4)
        denominator = choose(match_idx, t1 - (t2 - t1), t2 - t1, t2 - t1, t3 - t2, t4 - t3, t4 - t3)
        factor = choose(match_idx, self._previous_energy, e1 - self._previous_energy, e2 - e1, e3 - e2, e4 - e3, e4 - e3)

        if denominator == 0:
            return 0
        
        result = base + (adjustment / denominator) * factor
        return result

    @property
    def _ranks(self: "AdvancedMixin") -> Dict[str, int]:
        return {"Grandmaster" : 900, "Nova" : 1000, "Astra" : 1100, "Celestial" : 1200}


class Scenario:

    def __init__(self, name: str, thresholds: Tuple[int, int, int, int]) -> None:
        self.name = name
        self.thresholds = thresholds


class Benchmark(ABC):
    def __init__(self: "Benchmark", scenario_a: Optional[Scenario] = None, scenario_b: Optional[Scenario] = None, sub_benchmarks: Optional[Tuple["Benchmark", ...]] = None) -> None:

        if sub_benchmarks is None and not any([scenario_a is None, scenario_b is None]):
            self.scenario_a = scenario_a
            self.scenario_b = scenario_b
        elif scenario_a is None and scenario_b is None:
            self.sub_benchmark = sub_benchmarks
        else:
            raise Exception("No data provided in the constructor")

class NoviceBenchmark(Benchmark, NoviceMixin):
    pass

class IntermediateBenchmark(Benchmark, IntermediateMixin):
    pass

class AdvancedBenchmark(Benchmark, AdvancedMixin):
    pass

class Scenarios(Enum):

    # CLICKING
    vt_pasu_rasp_novice = Scenario(name="VT Pasu Rasp Novice", thresholds=(550,650,750,850))
    vt_pasu_rasp_intermediate = Scenario(name="VT Pasu Rasp Intermediate", thresholds=(750,850,950,1050))
    vt_pasu_rasp_advanced = Scenario(name="VT Pasu Rasp Advanced", thresholds=(940,1040,1120,1270))

    vt_bounceshot_novice = Scenario(name="VT Bounceshot Novice", thresholds=(500,600,700,800))
    vt_bounceshot_intermediate = Scenario(name="VT Bounceshot Intermediate", thresholds=(600,700,800,900))
    vt_bounceshot_advanced = Scenario(name="VT Bounceshot Advanced", thresholds=(800,900,1000,1150))

    vt_1w6ts_rasp_novice = Scenario(name="VT 1w6ts Rasp Novice", thresholds=(650,750,850,950))
    vt_1w5ts_rasp_intermediate = Scenario(name="VT 1w5ts Rasp Intermediate", thresholds=(1000,1100,1200,1300))
    vt_1w3ts_rasp_advanced = Scenario(name="VT 1w3ts Rasp Advanced", thresholds=(1280,1380,1460,1580))

    vt_multiclick_120_novice = Scenario(name="VT Multiclick 120 Novice", thresholds=(1160,1260,1360,1460))
    vt_multiclick_120_intermediate = Scenario(name="VT Multiclick 120 Intermediate", thresholds=(1360,1460,1560,1660))
    vt_multiclick_120_advanced = Scenario(name="VT Multiclick 120 Advanced", thresholds=(1630,1770,1890,2000))

    # TRACKING
    vt_smoothbot_novice = Scenario(name="VT Smoothbot Novice", thresholds=(2300,2500,3100,3500))
    vt_smoothbot_intermediate = Scenario(name="VT Smoothbot Intermediate", thresholds=(3050,3450,3850,4250))
    vt_smoothbot_advanced = Scenario(name="VT Smoothbot Advanced", thresholds=(3300,3600,3950,4300))
    
    vt_preciseorb_novice = Scenario(name="VT PreciseOrb Novice", thresholds=(1300,1600,1900,2200))
    vt_preciseorb_intermediate = Scenario(name="VT PreciseOrb Intermediate", thresholds=(1650,2050,2450,2850))
    vt_preciseorb_advanced = Scenario(name="VT PreciseOrb Advanced", thresholds=(2500,2850,3250,3650))

    vt_plaza_novice = Scenario(name="VT Plaza Novice", thresholds=(2150,2450,2850,3050))
    vt_plaza_intermediate = Scenario(name="VT Plaza Intermediate", thresholds=(2680,2980,3280,3530))
    vt_plaza_advanced = Scenario(name="VT Plaza Advanced", thresholds=(3275,3475,3600,3800))
    
    vt_air_novice = Scenario(name="VT Air Novice", thresholds=(1900,2200,2500,2800))
    vt_air_intermediate = Scenario(name="VT Air Intermediate", thresholds=(2450,2700,2950,3200))
    vt_air_advanced = Scenario(name="VT Air IntermedAdvancediate", thresholds=(3000,3250,3500,3750))
    
    # SWITCHING
    vt_psalmts_novice = Scenario(name="VT psalmTS Novice", thresholds=(620,690,760,830))
    vt_psalmts_intermediate = Scenario(name="VT psalmTS Intermediate", thresholds=(810,880,950,1020))
    vt_psalmts_advanced = Scenario(name="VT psalmTS Advanced", thresholds=(1080,1160,1200,1330))
    
    vt_skyts_novice = Scenario(name="VT skyTS Novice", thresholds=(780,860,950,1040))
    vt_skyts_intermediate = Scenario(name="VT skyTS Intermediate", thresholds=(1030,1130,1220,1300))
    vt_skyts_advanced = Scenario(name="VT skyTS Advanced", thresholds=(1300,1430,1500,1600))
    
    vt_evats_novice = Scenario(name="VT evaTS Novice", thresholds=(450,510,560,620))
    vt_evats_intermediate = Scenario(name="VT evaTS Intermediate", thresholds=(550,600,650,700))
    vt_evats_advanced = Scenario(name="VT evaTS Advanced", thresholds=(680,740,780,830))
    
    vt_bouncets_novice = Scenario(name="VT bounceTS Novice", thresholds=(490,550,610,680))
    vt_bouncets_intermediate = Scenario(name="VT bounceTS Intermediate", thresholds=(630,670,710,760))
    vt_bouncets_advanced = Scenario(name="VT bounceTS Advanced", thresholds=(820,920,970,1050))
    
    # STRAFING
    vt_anglestrafe_intermediate = Scenario(name="VT AngleStrafe Intermediate", thresholds=(740,830,920,1000))
    vt_anglestrafe_advanced = Scenario(name="VT AngleStrafe Advanced", thresholds=(880,1020,1150,1230))
    
    vt_arcstrafe_intermediate = Scenario(name="VT ArcStrafe Intermediate", thresholds=(660,750,850,940))
    vt_arcstrafe_advanced = Scenario(name="VT ArcStrafe Advanced", thresholds=(940,1080,1150,1230))
    
    vt_patstrafe_intermediate = Scenario(name="VT PatStrafe Intermediate", thresholds=(2260,2620,2800,3050))
    vt_patstrafe_advanced = Scenario(name="VT PatStrafe Advanced", thresholds=(3050,3240,3400,3500))
    
    vt_airstrafe_intermediate = Scenario(name="VT AirStrafe Intermediate", thresholds=(2800,3000,3200,3400))
    vt_airstrafe_advanced = Scenario(name="VT AirStrafe Advanced", thresholds=(3400,3600,3700,3825))

class Benchmarks(Enum):

    # CLICKING  
    nov_dyn_cli = NoviceBenchmark(scenario_a=Scenarios.vt_pasu_rasp_novice, scenario_b=Scenarios.vt_bounceshot_novice)
    int_dyn_cli = IntermediateBenchmark(scenario_a=Scenarios.vt_pasu_rasp_intermediate, scenario_b=Scenarios.vt_bounceshot_intermediate)
    adv_dyn_cli = AdvancedBenchmark(scenario_a=Scenarios.vt_pasu_rasp_advanced, scenario_b=Scenarios.vt_bounceshot_advanced)

    nov_sta_cli = NoviceBenchmark(scenario_a=Scenarios.vt_1w6ts_rasp_novice, scenario_b=Scenarios.vt_multiclick_120_novice)
    int_sta_cli = IntermediateBenchmark(scenario_a=Scenarios.vt_1w5ts_rasp_intermediate, scenario_b=Scenarios.vt_multiclick_120_intermediate)
    adv_sta_cli = AdvancedBenchmark(scenario_a=Scenarios.vt_1w3ts_rasp_advanced, scenario_b=Scenarios.vt_multiclick_120_advanced)

    # TRACKING
    nov_smo_tra = NoviceBenchmark(scenario_a=Scenarios.vt_smoothbot_novice, scenario_b=Scenarios.vt_preciseorb_novice)
    int_smo_tra = IntermediateBenchmark(scenario_a=Scenarios.vt_smoothbot_intermediate, scenario_b=Scenarios.vt_preciseorb_intermediate)
    adv_smo_tra = AdvancedBenchmark(scenario_a=Scenarios.vt_smoothbot_advanced, scenario_b=Scenarios.vt_preciseorb_advanced)

    nov_rea_tra = NoviceBenchmark(scenario_a=Scenarios.vt_plaza_novice, scenario_b=Scenarios.vt_air_novice)
    int_rea_tra = IntermediateBenchmark(scenario_a=Scenarios.vt_plaza_intermediate, scenario_b=Scenarios.vt_air_intermediate)
    adv_rea_tra = AdvancedBenchmark(scenario_a=Scenarios.vt_plaza_advanced, scenario_b=Scenarios.vt_air_advanced)

    # SWITCHING
    nov_spe_ts = NoviceBenchmark(scenario_a=Scenarios.vt_psalmts_novice, scenario_b=Scenarios.vt_skyts_novice)
    int_spe_ts = IntermediateBenchmark(scenario_a=Scenarios.vt_psalmts_intermediate, scenario_b=Scenarios.vt_skyts_intermediate)
    adv_spe_ts = AdvancedBenchmark(scenario_a=Scenarios.vt_psalmts_advanced, scenario_b=Scenarios.vt_skyts_advanced)

    nov_eva_ts = NoviceBenchmark(scenario_a=Scenarios.vt_evats_novice, scenario_b=Scenarios.vt_bouncets_novice)
    int_eva_ts = IntermediateBenchmark(scenario_a=Scenarios.vt_evats_intermediate, scenario_b=Scenarios.vt_bouncets_intermediate)
    adv_eva_ts = AdvancedBenchmark(scenario_a=Scenarios.vt_evats_advanced, scenario_b=Scenarios.vt_bouncets_advanced)

    # STRAFING
    int_str_cli = IntermediateBenchmark(scenario_a=Scenarios.vt_anglestrafe_intermediate, scenario_b=Scenarios.vt_arcstrafe_intermediate)
    adv_str_cli = AdvancedBenchmark(scenario_a=Scenarios.vt_anglestrafe_advanced, scenario_b=Scenarios.vt_arcstrafe_advanced)

    int_str_tra = IntermediateBenchmark(scenario_a=Scenarios.vt_patstrafe_intermediate, scenario_b=Scenarios.vt_airstrafe_intermediate)
    adv_str_tra = AdvancedBenchmark(scenario_a=Scenarios.vt_patstrafe_advanced, scenario_b=Scenarios.vt_airstrafe_advanced)
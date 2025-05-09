import json
import math
import sys
from itertools import combinations_with_replacement
from copy import deepcopy
from random import randrange, choice
from pc_configurator.models import Disc, Processor, Videocard, DiscType, Computer, CaseCooler, Certificate
from django.db import models
from django.db.models import Q, Avg, F, Value, ExpressionWrapper, FloatField, IntegerField
from django.db.models.functions import Cast
from django.db.models.fields.json import KT

#Возвращает словарь вида: интерфейс(ключ) - количество дисков(значение)
def count_discs_by_interface(discs):
    discs_count = {}
    for disc in discs:
        interface = disc.type.interface
        if interface in discs_count.keys():
            discs_count[interface] += 1
        else:
            discs_count[interface] = 1
    return discs_count
            
#Возвращает словарь вида: слот(ключ) - количество дисков(значение)
def count_discs_by_slot(discs):
    discs_count = {}
    for disc in discs:
        slot = disc.type.slot
        if slot in discs_count.keys():
            discs_count[slot] += 1
        else:
            discs_count[slot] = 1
    return discs_count

#Функция округления в большую сторону с учётом базы
def round_with_base(x, base):
    return base * math.ceil(x/base)

#Функция для подсчёта ближайшей реальной мощности блока питания
def needed_psu_power(power):
    return round_with_base(power, 50)

#Функция для подсчёта рекомендуемой мощности блока питания
def calculate_psu_power(assembly):
    cpu_tdp = assembly.processor.tdp
    videocard_tdp = assembly.videocard.psu_power
    memory_cnt = assembly.memory_cnt
    if memory_cnt is None:
        raise ValueError('Memory count is not valid.')
    discs_count = len(assembly.discs)
    if discs_count == 0:
        raise ValueError('Discs count is not valid.')
    casecoolers = json.loads(assembly.casecoolers)
    casecoolers_count = 0
    for side in casecoolers:
        if 'count' in casecoolers[side].keys():
            casecoolers_count += casecoolers[side]['count']
    return needed_psu_power((cpu_tdp * 1.87 + videocard_tdp / 2 + memory_cnt * 4 + discs_count * 15 + casecoolers_count * 5) * 1.67)

#Функция для возврата описания ошибки по её коду
def get_error_desciption(index):
    errors = {
        1 : "Сокет процессора не совпадает с сокетом материнской платы.",
        2 : "Кулер несовместим с процессором.",
        3 : "Выбранный процессор не имеет графического ускорителя. Добавьте видеокарту в сборку.",
        4 : "Мощности кулера недостаточно для охлаждения процессора.",
        5 : "Кулер несовместим с сокетом материнской платы.",
        6 : "Материнская плата имеет несовместимый с корпусом форм-фактор.",
        7 : "Количество модулей оперативной памяти превышает число слотов.",
        8 : "Версия интерфейса PCI-E видеокарты превышает версию интерфейса материнской платы.",
        9 : "Тип оперативной памяти не совместим с материнской платой.",
        10 : "Количество дисков SATA превышает количество SATA-портов.",
        11 : "Количество дисков M.2 превышает количество M.2-слотов.",
        12 : "Разъём питания процессора на материнской плате отсутствует на выбранном блоке питания.",
        13 : "В корпусе недостаточно слотов расширения для установки выбранной видеокарты.",
        14 : "В корпусе недостаточно места для установки выбранной видеокарты.",
        15 : "Блок питания не имеет достаточного количества портов для питания видеокарты.",
        16 : "Кулер слишком высокий для выбранного корпуса.",
        17 : "В корпусе недостаточно места для установки всех дисков 3.5'.",
        18 : "В корпусе недостаточно места для установки всех дисков 2.5'.",
        19 : "В корпусе недостаточно места для установки всех вентиляторов.",
        20 : "Типоразмер выбранного блока питания несовместим с корпусом.",
        21 : "В корпусе недостаточно места для блока питания.",
        22 : "Блок питания не имеет достаточного числа коннекторов SATA.",
        23 : "Мощности блока питания недостаточно для питания всех комплектующих.",
    }
    return errors[index]

def get_warning_desciption(index):
    warnings = {
        1 : "Для подключения кулера и всех вентиляторов потребуется разветвитель 4-pin PWM.",
    }
    return warnings[index]

#Далее представлены различные функции проверки комплектующих на совместимость. Для каждой функции приведено назначение проверки и код соответствующей ошибки.
#Проверка совместимости сокетов мат.платы и процессора. (Код ошибки: 1)
def correct_pxm_socket(assembly):
    if assembly.processor is not None and assembly.motherboard is not None:
        if assembly.processor.socket != assembly.motherboard.socket:
            return False
        else:
            return True

#Проверка совместимости кулера и процессора. (Код ошибки: 2)
def correct_cxp_socket(assembly):
    if assembly.processor is not None and assembly.cooler is not None:
        if assembly.processor.socket not in assembly.cooler.sockets:
            return False
        else:
            return True

#Проверка наличия графического процессора в сборке. (Код ошибки: 3)
def exist_graphics(assembly):
    if assembly.processor is not None:
        if assembly.videocard is None and not assembly.processor.int_graphics:
            return False
        else:
            return True

#Проверка достаточности мощности процессорного кулера. (Код ошибки: 4)
def correct_cooler_power(assembly):
    if assembly.processor is not None and assembly.cooler is not None:
        if assembly.processor.tdp * 1.1 > assembly.cooler.power:
            return False
        else:
            return True

#Проверка совместимости кулера и материнской платы. (Код ошибки: 5)
def correct_cxm_socket(assembly):
    if assembly.motherboard is not None and assembly.cooler is not None:
        if assembly.motherboard.socket not in assembly.cooler.sockets:
            return False
        else:
            return True

#Проверка совместимости материнской платы и корпуса. (Код ошибки: 6)
def correct_motherboard_ff(assembly):
    if assembly.motherboard is not None and assembly.case is not None:
        if assembly.motherboard.formfactor not in assembly.case.mb_ffs:
            return False
        else:
            return True

#Проверка достаточности количества слотов оперативной памяти. (Код ошибки: 7)
def correct_motherboard_memslots(assembly):
    if assembly.motherboard is not None and assembly.memory_cnt is not None:
        if assembly.memory_cnt > assembly.motherboard.mem_slots:
            return False
        else:
            return True

#Проверка старшинства версий PCI-E материнской платы и видеокарты. (Код ошибки: 8)
def correct_motherboard_pciever(assembly):
    if assembly.motherboard is not None and assembly.videocard is not None:
        if assembly.videocard.pciex16_ver > assembly.motherboard.pciex16_ver:
            return False
        else:
            return True

#Проверка достаточности количества слотов оперативной памяти. (Код ошибки: 9)
def correct_motherboard_memtype(assembly):
    if assembly.motherboard is not None and assembly.memory is not None:
        if assembly.memory.mem_type != assembly.motherboard.mem_type:
            return False
        else:
            return True

#Проверка достаточности количества портов SATA. (Код ошибки: 10)
def correct_motherboard_sata(assembly):
    if assembly.motherboard is not None and len(assembly.discs) > 0:
        discs = count_discs_by_interface(list(map(lambda index: Disc.objects.get(pk=index), assembly.discs)))
        if 'SATA' in discs.keys() and discs['SATA'] > assembly.motherboard.sata_ports:
            return False
        else:
            return True

#Проверка достаточности количества слотов M.2. (Код ошибки: 11)
def correct_motherboard_m2(assembly):
    if assembly.motherboard is not None and len(assembly.discs) > 0:
        discs = count_discs_by_interface(list(map(lambda index: Disc.objects.get(pk=index), assembly.discs)))
        if 'PCI-E M.2' in discs.keys() and discs['PCI-E M.2'] > assembly.motherboard.m2_slots:
            return False
        else:
            return True

#Проверка наличия коннектора питания процессора на блоке питания. (Код ошибки: 12)
def correct_motherboard_atx12v(assembly):
    if assembly.motherboard is not None and assembly.powersupply is not None:
        powersupply_connectors = json.loads(assembly.powersupply.connectors)
        motherboard_connectors = json.loads(assembly.motherboard.connectors)
        if (('4-pin atx-12v' in motherboard_connectors.keys() and 'CPU/4' not in powersupply_connectors.keys() and 'CPU/4+4' not in powersupply_connectors.keys()) or
            ('8-pin atx-12v' in motherboard_connectors.keys() and 'CPU/8' not in powersupply_connectors.keys() and 'CPU/4+4' not in powersupply_connectors.keys())):
            return False
        else:
            return True

#Проверка достаточности слотов расширения в корпусе. (Код ошибки: 13)
def correct_case_exp(assembly):
    if assembly.videocard is not None and assembly.case is not None:
        if assembly.case.exp_slots < assembly.videocard.exp_slots:
            return False
        else:
            return True

#Проверка максимальной длины видеокарты. (Код ошибки: 14)
def correct_case_vlen(assembly):
    if assembly.videocard is not None and assembly.case is not None:
        if assembly.case.max_gpu_length < assembly.videocard.length:
            return False
        else:
            return True

#Проверка наличия коннектора питания для видеокарты на блоке питания. (Код ошибки: 15)
def correct_videocard_connector(assembly):
    if assembly.videocard is not None and assembly.powersupply is not None:
        videocard = assembly.videocard
        powersupply = assembly.powersupply
        if videocard.power_pins is not None:
            videocard_power_pins = json.loads(videocard.power_pins)
            powersupply_connectors = json.loads(powersupply.connectors)
            gpu_6pin = videocard_power_pins['6-pin'] if '6-pin' in videocard_power_pins.keys() else 0
            gpu_8pin = videocard_power_pins['8-pin'] if '8-pin' in videocard_power_pins.keys() else 0
            gpu_16pin = videocard_power_pins['16-pin'] if '16-pin' in videocard_power_pins.keys() else 0
            psu_6pin = powersupply_connectors['GPU/6'] if 'GPU/6' in powersupply_connectors.keys() else 0
            psu_6p2pin = powersupply_connectors['GPU/6+2'] if 'GPU/6+2' in powersupply_connectors.keys() else 0
            psu_8pin = powersupply_connectors['GPU/8'] if 'GPU/8' in powersupply_connectors.keys() else 0
            psu_16pin = (powersupply_connectors['GPU/12+4/12VHPWR'] if 'GPU/12+4/12VHPWR' in powersupply_connectors.keys() else 0 +
                         powersupply_connectors['GPU/12+4/12V-2х6'] if 'GPU/12+4/12V-2х6' in powersupply_connectors.keys() else 0)
            if psu_16pin < gpu_16pin:
                return False
            elif ((psu_6pin < gpu_6pin or psu_8pin < gpu_8pin) and 
                 ((gpu_6pin - psu_6pin) if (gpu_6pin - psu_6pin) > 0 else 0) + ((gpu_8pin - psu_8pin) if (gpu_8pin - psu_8pin) > 0 else 0) > psu_6p2pin):
                return False
            else:
                return True
        else:
            return True

#Проверка максимальной высоты кулера. (Код ошибки: 16)
def correct_cooler_height(assembly):
    if assembly.cooler is not None and assembly.case is not None:
        if assembly.cooler.height > assembly.case.max_cooler_height:
            return False
        else:
            return True

#Проверка достаточности количества слотов 3.5'. (Код ошибки: 17)
def correct_case_bigsata(assembly):
    if assembly.case is not None and len(assembly.discs) > 0:
        discs = count_discs_by_slot(list(map(lambda index: Disc.objects.get(pk=index), assembly.discs)))
        if 'big' in discs.keys() and assembly.case.big_sata_slots < discs['big']:
            return False
        else:
            return True

#Проверка достаточности количества слотов 2.5'. (Код ошибки: 18)
def correct_case_smallsata(assembly):
    if assembly.case is not None and len(assembly.discs) > 0:
        discs = count_discs_by_slot(list(map(lambda index: Disc.objects.get(pk=index), assembly.discs)))
        if 'small' in discs.keys() and assembly.case.small_sata_slots < discs['small']:
            return False
        else:
            return True

#Проверка достаточности места для корпусных вентиляторов. (Код ошибки: 19)
def correct_case_coolers(assembly):
    if assembly.case is not None and assembly.casecoolers is not None:
        if assembly.case.cooler_slots is not None:
            casecoolers = json.loads(assembly.casecoolers)
            slots = json.loads(assembly.case.cooler_slots)
            for side in casecoolers.keys():
                assembly_side = casecoolers[side]
                case_side = slots[side]
                if 'count' in assembly_side.keys() and 'size' in assembly_side.keys() and 'count' in case_side.keys() and 'size' in case_side.keys() and assembly_side['count'] * assembly_side['size'] > case_side['count'] * case_side['size']:
                    return False
                else:
                    return True

#Проверка совместимости блока питания с корпусом. (Код ошибки: 20)
def correct_powersupply_typesize(assembly):
    if assembly.case is not None and assembly.powersupply is not None:
        if assembly.powersupply.typesize not in assembly.case.psu_typesize:
            return False
        else:
            return True

#Проверка достаточности места для блока питания. (Код ошибки: 21)
def correct_powersupply_len(assembly):
    if assembly.case is not None and assembly.powersupply is not None:
        if assembly.case.max_psu_length is not None and assembly.powersupply.length is not None and assembly.case.max_psu_length < assembly.powersupply.length:
            return False
        else:
            return True

#Проверка достаточности коннекторов SATA у блока питания. (Код ошибки: 22)
def correct_powersupply_sata(assembly):
    if assembly.powersupply is not None and len(assembly.discs) > 0:
        discs = list(map(lambda index: Disc.objects.get(pk=index).type.slot, assembly.discs))
        count = 0
        for disc in discs:
            if disc != 'M.2':
                count += 1
        if json.loads(assembly.powersupply.connectors)['SATA'] < count:
            return False
        else:
            return True

#Проверка достаточности мощности блока питания. (Код ошибки: 23)
def correct_powersupply_power(assembly):
    if assembly.powersupply is not None:
        if calculate_psu_power(assembly) > assembly.powersupply.power:
            return False
        else:
            return True

#Проверка достаточности количества коннекторов 4-pin PWM на материнской плате. (Код предупреждения: 1)
def enough_motherboard_4pin(assembly):
    if assembly.motherboard is not None and assembly.casecoolers is not None:
        motherboard_connectors = json.loads(assembly.motherboard.connectors)
        casecoolers = json.loads(assembly.casecoolers)
        total_count = 0
        for side in casecoolers.keys():
            if len(casecoolers[side].keys()) > 0:
                total_count += casecoolers[side]['count']
        if '4-pin pwm' in motherboard_connectors.keys() and motherboard_connectors['4-pin pwm'] < total_count + 1:
            return False
        else:
            return True

#Полная проверка совместимости компонентов сборки
def check_compatibility(assembly):
    errors = []
    warnings = []
    if not correct_pxm_socket(assembly):
        errors.append(1)
    if not correct_cxp_socket(assembly):
        errors.append(2)
    if not exist_graphics(assembly):
        errors.append(3)
    if not correct_cooler_power(assembly):
        errors.append(4)
    if not correct_cxm_socket(assembly):
        errors.append(5)
    if not correct_motherboard_ff(assembly):
        errors.append(6)
    if not correct_motherboard_memslots(assembly):
        errors.append(7)
    if not correct_motherboard_pciever(assembly):
        errors.append(8)
    if not correct_motherboard_memtype(assembly):
        errors.append(9)
    if not correct_motherboard_sata(assembly):
        errors.append(10)
    if not correct_motherboard_m2(assembly):
        errors.append(11)
    if not correct_motherboard_atx12v(assembly):
        errors.append(12)
    if not correct_case_exp(assembly):
        errors.append(13)
    if not correct_case_vlen(assembly):
        errors.append(14)
    if not correct_videocard_connector(assembly):
        errors.append(15)
    if not correct_cooler_height(assembly):
        errors.append(16)
    if not correct_case_bigsata(assembly):
        errors.append(17)
    if not correct_case_smallsata(assembly):
        errors.append(18)
    if not correct_case_coolers(assembly):
        errors.append(19)
    if not correct_powersupply_typesize(assembly):
        errors.append(20)
    if not correct_powersupply_len(assembly):
        errors.append(21)
    if not correct_powersupply_sata(assembly):
        errors.append(22)
    if not correct_powersupply_power(assembly):
        errors.append(23)
    if not enough_motherboard_4pin(assembly):
        warnings.append(1)
    return [len(errors) == 0, errors, warnings]

#Проверка наличия необходимых компонентов в сборке
def check_existance(assembly):
    if (
        assembly.processor is None or
        assembly.motherboard is None or
        assembly.memory is None or
        assembly.memory_cnt is None or
        assembly.powersupply is None or
        assembly.case is None or
        assembly.cooler is None or
        len(assembly.discs) == 0
    ):
        return False
    else:
        return True

#Проверка корректности сборки
def assembly_is_valid(assembly):
    if check_existance(assembly):
        buf = check_compatibility(assembly)
        return [buf[0], buf[1], buf[2]]
    else:
        return [False, [], []]

def check_qs(queryset):
    if len(queryset) == 0:
        raise ValueError("Can not assemble pc with entered chars.")
    else:
        return

def parse_combination(combination_str):
    comb_list = list(map(lambda x: int(x), combination_str.split('/')))
    combination = {}
    combination['processor'] = Processor.objects.get(pk=comb_list[0])
    combination['videocard'] = Videocard.objects.get(pk=comb_list[1])
    return combination

def slice_by_price(combs, combinations, count):
    combs_list = deepcopy(combs)
    for comb in combs_list.keys():
        combs_list[comb] = combinations[comb]['price']
    combs_list = dict(sorted(combs_list.items(), key=lambda item: item[1]))
    combs_list = dict(list(combs_list.items())[:count])
    return combs_list

def slice_by_price_base(combs, combinations, max_base):
    combs_list = deepcopy(combs)
    for comb in combs_list.keys():
        combs_list[comb] = combinations[comb]['price']
    combs_list = dict(sorted(combs_list.items(), key=lambda item: item[1]))
    keys = list(combs_list.keys())
    max_price = combs_list[keys[0]] * max_base
    max_inc = len(keys) - 1
    inc = -1
    flag = False
    while not flag and inc < max_inc:
        inc += 1
        if combs_list[keys[inc]] > max_price:
            flag = True
    if inc == max_inc:
        combs_list = dict(list(combs_list.items())[:])
    else:
        combs_list = dict(list(combs_list.items())[:inc])
    return combs_list

def slice_by_rating(combs, combinations, count):
    combs_list = deepcopy(combs)
    for comb in combs_list.keys():
        combs_list[comb] = combinations[comb]['rating']
    combs_list = dict(sorted(combs_list.items(), key=lambda item: item[1], reverse=True))
    combs_list = dict(list(combs_list.items())[:count])
    return combs_list

def slice_by_rtp(combs, combinations, count):
    combs_list = deepcopy(combs)
    for comb in combs_list.keys():
        combs_list[comb] = combinations[comb]['rtp']
    combs_list = dict(sorted(combs_list.items(), key=lambda item: item[1], reverse=True))
    combs_list = dict(list(combs_list.items())[:count])
    return combs_list

def slice_by_rtp_final(combs, combinations):
    combs_list = deepcopy(combs)
    for comb in combs_list.keys():
        combs_list[comb] = combinations[comb]['rtp']
    combs_list = dict(sorted(combs_list.items(), key=lambda item: item[1], reverse=True))
    keys = list(combs_list.keys())
    min_rtp = combs_list[keys[0]] * 0.8
    max_inc = len(keys) - 1
    inc = -1
    flag = False
    while not flag and inc < max_inc:
        inc += 1
        if combs_list[keys[inc]] < min_rtp:
            flag = True
    if inc == max_inc:
        combs_list = dict(list(combs_list.items())[:])
    else:
        combs_list = dict(list(combs_list.items())[:inc])
    return combs_list

def cheap_combinations(combs, combinations):
    combs_list = deepcopy(combs)
    combs_list = slice_by_price_base(combs_list, combinations, 1.25)
    while len(combs_list) > 20:
        combs_list = slice_by_rtp(combs_list, combinations, max(40, round(len(combs_list) / 4)))
        combs_list = slice_by_rating(combs_list, combinations, max(20, round(len(combs_list) / 2)))
    combs_list = slice_by_price(combs_list, combinations, 10)
    combs_list = slice_by_rtp_final(combs_list, combinations)
    return combs_list

def optimal_combinations(combs, combinations):
    combs_list = deepcopy(combs)
    combs_list = slice_by_price_base(combs_list, combinations, 1.5)
    while len(combs_list) > 20:
        combs_list = slice_by_rating(combs_list, combinations, max(40, round(len(combs_list) / 3)))
        combs_list = slice_by_rtp(combs_list, combinations, max(20, round(len(combs_list) / 3)))
    combs_list = slice_by_rating(combs_list, combinations, 10)
    combs_list = slice_by_rtp_final(combs_list, combinations)
    return combs_list

def performant_combinations(combs, combinations):
    combs_list = deepcopy(combs)
    combs_list = slice_by_price_base(combs_list, combinations, 2)
    while len(combs_list) > 20:
        combs_list = slice_by_rtp(combs_list, combinations, max(40, round(len(combs_list) / 2)))
        combs_list = slice_by_rating(combs_list, combinations, max(20, round(len(combs_list) / 4)))
    combs_list = slice_by_price(combs_list, combinations, 10)
    combs_list = slice_by_rtp_final(combs_list, combinations)
    return combs_list

def best_combinations(combs, combinations):
    combs_list = deepcopy(combs)
    return {'cheap' : list(cheap_combinations(combs_list, combinations).keys())[0],
            'optimal' : list(optimal_combinations(combs_list, combinations).keys())[0],
            'performant' : list(performant_combinations(combs_list, combinations).keys())[0]}

def rand_combinations(combs, combinations):
    combs_list = deepcopy(combs)
    cheap = list(cheap_combinations(combs_list, combinations).keys())
    optimal = list(optimal_combinations(combs_list, combinations).keys())
    performant = list(performant_combinations(combs_list, combinations).keys())
    return {'cheap' : cheap[randrange(0, len(cheap))],
            'optimal' : optimal[randrange(0, len(optimal))],
            'performant' : performant[randrange(0, len(performant))]}

def find_combinations(cpu_qs, gpu_qs, random = False):
    combinations = {}
    for cpu in cpu_qs:
        for gpu in gpu_qs:
            ratio = cpu.rating / gpu.rating
            if ratio < 1.81 and ratio > 0.4:
                rating = cpu.rating + gpu.rating
                price = cpu.price + gpu.price
                chars = {'ratio' : ratio, 'price' : price, 'rating' : rating}
                combinations[f'{cpu.id}/{gpu.id}'] = chars
    min_price = sys.maxsize
    max_price = 0
    min_rate = sys.maxsize
    max_rate = 0
    for comb in combinations.values():
        if comb['price'] > max_price:
            max_price = comb['price']
        if comb['price'] < min_price:
            min_price = comb['price']
        if comb['rating'] > max_rate:
            max_rate = comb['rating']
        if comb['rating'] < min_rate:
            min_rate = comb['rating']
    k = (max_price / min_price) / (max_rate / min_rate)
    for comb in combinations.keys():
        combinations[comb]['rtp'] = (min_rate + (combinations[comb]['rating'] - min_rate) * k) / combinations[comb]['price']
    combs = {}
    for comb in combinations.keys():
        combs[comb] = 0
    if random:
        best = rand_combinations(combs, combinations)
    else:
        best = best_combinations(combs, combinations)
    for key in best.keys():
        best[key] = parse_combination(best[key])
    return best

def find_disc_combination(storage_options, required_volume, min_ssd_volume, max_m2_disks, max_2_5_slots, max_3_5_slots, max_sata_ports):
    for dt in storage_options.keys():
        volumes = list(storage_options[dt].keys())
        for vol in volumes:
            if ((vol > required_volume and volumes.index(vol) != 0) or (vol < required_volume // 2 and volumes.index(vol) != len(volumes)-1)) and ((vol > min_ssd_volume and volumes.index(vol) != 0) or (vol < min_ssd_volume // 2 and volumes.index(vol) != len(volumes)-1)):
                del(storage_options[dt][vol])
    best_cost = float('inf')
    best_combination = None
    all_storage = []
    for storage_type in storage_options:
        for volume in storage_options[storage_type]:
            all_storage.append((storage_type, volume))
    for disc_cnt in range(1, max_m2_disks + min(max_sata_ports, max_2_5_slots + max_3_5_slots) + 1):
        for combination in combinations_with_replacement(all_storage, disc_cnt):
            total_volume = sum(item[1] for item in combination)
            m2_count = sum(1 for item in combination if item[0] == 'M.2 SSD')
            sata_count = sum(1 for item in combination if item[0] in ['2.5" SSD', '2.5" HDD', '3.5" HDD'])
            hdd_2_5_count = sum(1 for item in combination if item[0] == '2.5" HDD')
            hdd_3_5_count = sum(1 for item in combination if item[0] == '3.5" HDD')
            ssd_volume = sum(item[1] for item in combination if item[0] in ['M.2 SSD', '2.5" SSD'])
            if (total_volume >= required_volume and 
                ssd_volume >= min_ssd_volume and 
                m2_count <= max_m2_disks and 
                hdd_2_5_count <= max_2_5_slots and 
                hdd_3_5_count <= max_3_5_slots and
                sata_count <= max_sata_ports):
                
                total_cost = sum(storage_options[item[0]][item[1]] * (item[1] / 1024) for item in combination)
                if total_cost < best_cost:
                    best_cost = total_cost
                    best_combination = combination
    return best_combination

def check_connectors(gpu, mb, psu):
    powersupply_connectors = json.loads(psu.connectors)
    if gpu.power_pins is not None:
        videocard_power_pins = json.loads(gpu.power_pins)
        gpu_6pin = videocard_power_pins['6-pin'] if '6-pin' in videocard_power_pins.keys() else 0
        gpu_8pin = videocard_power_pins['8-pin'] if '8-pin' in videocard_power_pins.keys() else 0
        gpu_16pin = videocard_power_pins['16-pin'] if '16-pin' in videocard_power_pins.keys() else 0
        psu_6pin = powersupply_connectors['GPU/6'] if 'GPU/6' in powersupply_connectors.keys() else 0
        psu_6p2pin = powersupply_connectors['GPU/6+2'] if 'GPU/6+2' in powersupply_connectors.keys() else 0
        psu_8pin = powersupply_connectors['GPU/8'] if 'GPU/8' in powersupply_connectors.keys() else 0
        psu_16pin = (powersupply_connectors['GPU/12+4/12VHPWR'] if 'GPU/12+4/12VHPWR' in powersupply_connectors.keys() else 0 +
                        powersupply_connectors['GPU/12+4/12V-2х6'] if 'GPU/12+4/12V-2х6' in powersupply_connectors.keys() else 0)
        if psu_16pin < gpu_16pin:
            return False
        elif ((psu_6pin < gpu_6pin or psu_8pin < gpu_8pin) and 
                ((gpu_6pin - psu_6pin) if (gpu_6pin - psu_6pin) > 0 else 0) + ((gpu_8pin - psu_8pin) if (gpu_8pin - psu_8pin) > 0 else 0) > psu_6p2pin):
            return False
    motherboard_connectors = json.loads(mb.connectors)
    if (('4-pin atx-12v' in motherboard_connectors.keys() and 'CPU/4' not in powersupply_connectors.keys() and 'CPU/4+4' not in powersupply_connectors.keys()) or
        ('8-pin atx-12v' in motherboard_connectors.keys() and 'CPU/8' not in powersupply_connectors.keys() and 'CPU/4+4' not in powersupply_connectors.keys())):
        return False
    return True
    

def find_necessaries(combination, querysets, selected_params, mode, random = False):
    selected_cpu = combination['processor']
    selected_gpu = combination['videocard']
    motherboard_qs = querysets['motherboard']
    memory_qs = querysets['memory']
    cooler_qs = querysets['cooler']
    case_qs = querysets['case']
    disc_qs = querysets['disc']
    casecooler_qs = querysets['casecooler']
    powersupply_qs = querysets['powersupply']
    min_ram_vol = selected_params['min_ram_volume']
    cooler_mult = selected_params['cooler_mult']
    any_volume = selected_params['any_volume']
    ssd_volume = selected_params['ssd_volume']
    motherboard_qs = motherboard_qs.filter(socket = selected_cpu.socket).filter(pciex16_ver__gte = selected_gpu.pciex16_ver)
    mem_types = motherboard_qs.order_by('mem_type').values_list('mem_type', flat=True).distinct()
    max_vol_per_type = {}
    for mem_type in mem_types:
        volume = {}
        max_module_vol = memory_qs.filter(mem_type = mem_type).order_by('-volume').first().volume
        max_ram_slots = motherboard_qs.filter(mem_type = mem_type).order_by('-mem_slots').first().mem_slots
        volume['max_volume'] = max_module_vol * max_ram_slots
        volume['needed_slots'] = max_ram_slots
        max_vol_per_type[mem_type] = volume
    mb_filter = Q()
    mem_filter = Q()
    for mem_type in max_vol_per_type.keys():
        if max_vol_per_type[mem_type]['max_volume'] >= min_ram_vol:
            slots = 1
            flag = False
            while slots <= max_vol_per_type[mem_type]['needed_slots'] and not flag:
                if max_vol_per_type[mem_type]['max_volume'] / max_vol_per_type[mem_type]['needed_slots'] * slots >= min_ram_vol:
                    flag = True
                else:
                    slots *= 2
            mb_filter = mb_filter | (Q(mem_type = mem_type) & Q(mem_slots__gte = slots))
            mem_filter = mem_filter | Q(mem_type = mem_type)
    if len(mb_filter) == 0 or len(mem_filter) == 0:
        raise ValueError("Can not assemble pc with entered chars.")
    motherboard_qs = motherboard_qs.filter(mb_filter)
    memory_qs = memory_qs.filter(mem_filter)
    min_mb_price = motherboard_qs.order_by('price').values_list('price', flat=True)[0]
    if mode == 'cheap':
        motherboard_qs = motherboard_qs.filter(price__lte = min_mb_price * 1.25)
    elif mode == 'optimal':
        motherboard_qs = motherboard_qs.filter(price__lte = min_mb_price * 1.5)
    elif mode == 'performant':
        motherboard_qs = motherboard_qs.filter(price__lte = min_mb_price * 2)
    else:
        raise ValueError('Mode does not exist.')
    #Выборка материнских плат по метрике !!!
    pks = list(motherboard_qs.values_list('id', flat=True))
    random_pk = choice(pks)
    selected_mb = motherboard_qs.get(pk=random_pk)
    combination['motherboard'] = selected_mb
    memory_qs = memory_qs.filter(mem_type = selected_mb.mem_type)
    module_volumes = memory_qs.order_by('volume').values_list('volume', flat=True).distinct()
    max_module_vol = max(module_volumes)
    mod_cnt = max_vol_per_type[mem_type]['needed_slots']
    vol_cnt_combs = {}
    while mod_cnt >= math.ceil(min_ram_vol / max_module_vol):
        temp_vol = round(min_ram_vol / mod_cnt)
        for vol in module_volumes:
            if vol >= temp_vol:
                vol_cnt_combs[mod_cnt] = vol
                break
        if vol_cnt_combs[mod_cnt] == max_module_vol:
            break
        else:
            mod_cnt //= 2
    best_count = 0
    if mode == 'cheap':
        avg_price = sys.maxsize
        for mod_count_key in vol_cnt_combs.keys():
            temp_avg_price = memory_qs.filter(volume = vol_cnt_combs[mod_count_key]).aggregate(Avg("price", default=0))['price__avg'] * mod_count_key
            if temp_avg_price < avg_price:
                avg_price = temp_avg_price
                best_count = mod_count_key
    elif mode == 'optimal' or mode == 'performant':
        buf = max_vol_per_type[mem_type]['needed_slots'] // 2
        best_count = buf if buf in vol_cnt_combs.keys() else min(vol_cnt_combs.keys())
    combination['memory_cnt'] = best_count
    memory_qs = memory_qs.filter(volume = vol_cnt_combs[best_count])
    if mode == 'cheap':
        memory_qs = memory_qs.filter(price__lte = memory_qs.order_by('price').first().price + (memory_qs.order_by('-price').first().price - memory_qs.order_by('price').first().price) / 4)
    elif mode == 'optimal':
        memory_qs = memory_qs.filter(price__lte = memory_qs.order_by('price').first().price + (memory_qs.order_by('-price').first().price - memory_qs.order_by('price').first().price) / 2)
    min_bandwidth = memory_qs.order_by('bandwidth').first().bandwidth
    max_bandwidth = memory_qs.order_by('-bandwidth').first().bandwidth
    min_price = memory_qs.order_by('price').first().price
    max_price = memory_qs.order_by('-price').first().price
    k = (max_price / min_price) / (max_bandwidth / min_bandwidth)
    memory_qs = memory_qs.annotate(metrics=(min_bandwidth + (F('bandwidth') - min_bandwidth) * k) / F('price'))
    if mode == 'cheap':
        while len(memory_qs) > 20:
            memory_qs = sorted(memory_qs, key=lambda obj: obj.metrics, reverse=True)[:max(40, round(len(memory_qs) / 4))]
            memory_qs = sorted(memory_qs, key=lambda obj: obj.bandwidth, reverse=True)[:max(20, round(len(memory_qs) / 2))]
        memory_qs = sorted(memory_qs, key=lambda obj: obj.price)[:10]
    elif mode == 'optimal':
        while len(memory_qs) > 20:
            memory_qs = sorted(memory_qs, key=lambda obj: obj.bandwidth, reverse=True)[:max(40, round(len(memory_qs) / 3))]
            memory_qs = sorted(memory_qs, key=lambda obj: obj.metrics, reverse=True)[:max(20, round(len(memory_qs) / 3))]
        memory_qs = sorted(memory_qs, key=lambda obj: obj.price)[:10]
    else:
        while len(memory_qs) > 20:
            memory_qs = sorted(memory_qs, key=lambda obj: obj.bandwidth, reverse=True)[:max(40, round(len(memory_qs) / 4))]
            memory_qs = sorted(memory_qs, key=lambda obj: obj.metrics, reverse=True)[:max(20, round(len(memory_qs) / 2))]
        memory_qs = sorted(memory_qs, key=lambda obj: [obj.bandwidth, -obj.latency], reverse=True)[:10]
    if random:
        combination['memory'] = choice(memory_qs)
    else:
        combination['memory'] = memory_qs[0]
    cooler_qs = cooler_qs.filter(sockets__contains = [selected_cpu.socket]).filter(power__gte = selected_cpu.tdp * 1.1 * cooler_mult)
    check_qs(cooler_qs)
    if mode == 'cheap':
        cooler_qs = cooler_qs.filter(price__lte = cooler_qs.order_by('price').first().price + (cooler_qs.order_by('-price').first().price - cooler_qs.order_by('price').first().price) / 4)
    elif mode == 'optimal':
        cooler_qs = cooler_qs.filter(price__lte = cooler_qs.order_by('price').first().price + (cooler_qs.order_by('-price').first().price - cooler_qs.order_by('price').first().price) / 2)
    min_power = cooler_qs.order_by('power').first().power
    max_power = cooler_qs.order_by('-power').first().power
    min_price = cooler_qs.order_by('price').first().price
    max_price = cooler_qs.order_by('-price').first().price
    k = (max_price / min_price) / (max_power / min_power)
    cooler_qs = cooler_qs.annotate(metrics=(min_power + (F('power') - min_power) * k) / F('price'))
    if mode == 'cheap':
        while len(cooler_qs) > 20:
            cooler_qs = sorted(cooler_qs, key=lambda obj: obj.metrics, reverse=True)[:max(40, round(len(cooler_qs) / 4))]
            cooler_qs = sorted(cooler_qs, key=lambda obj: obj.power, reverse=True)[:max(20, round(len(cooler_qs) / 2))]
        cooler_qs = sorted(cooler_qs, key=lambda obj: obj.price)[:10]
    elif mode == 'optimal':
        while len(cooler_qs) > 20:
            cooler_qs = sorted(cooler_qs, key=lambda obj: obj.power, reverse=True)[:max(40, round(len(cooler_qs) / 3))]
            cooler_qs = sorted(cooler_qs, key=lambda obj: obj.metrics, reverse=True)[:max(20, round(len(cooler_qs) / 3))]
        cooler_qs = sorted(cooler_qs, key=lambda obj: obj.price)[:10]
    else:
        while len(cooler_qs) > 20:
            cooler_qs = sorted(cooler_qs, key=lambda obj: obj.power, reverse=True)[:max(40, round(len(cooler_qs) / 4))]
            cooler_qs = sorted(cooler_qs, key=lambda obj: obj.metrics, reverse=True)[:max(20, round(len(cooler_qs) / 2))]
        cooler_qs = sorted(cooler_qs, key=lambda obj: obj.power, reverse=True)[:10]
        cooler_qs = sorted(cooler_qs, key=lambda obj: obj.metrics, reverse=True)
    if random:
        combination['cooler'] = choice(cooler_qs)
    else:
        combination['cooler'] = cooler_qs[0]

    case_qs = case_qs.filter(
        Q(mb_ffs__contains = [selected_mb.formfactor]) &
        Q(max_gpu_length__gte = selected_gpu.length) &
        Q(max_cooler_height__gte = combination['cooler'].height) &
        Q(exp_slots__gte = selected_gpu.exp_slots)
    )
    #Выбор корпуса по метрике !!!
    selected_case = choice(case_qs)
    combination['case'] = selected_case

    sys_ssd = disc_qs.filter(type = DiscType.objects.get(name = 'M.2 SSD'))
    check_qs(sys_ssd)
    if mode == 'cheap':
        sys_ssd = sys_ssd.filter(
            Q(price__lte = sys_ssd.order_by('price').first().price + (sys_ssd.order_by('-price').first().price - sys_ssd.order_by('price').first().price) / 4) &
            Q(volume__lt = 512)
        )
    elif mode == 'optimal':
        sys_ssd = sys_ssd.filter(
            Q(price__lte = sys_ssd.order_by('price').first().price + (sys_ssd.order_by('-price').first().price - sys_ssd.order_by('price').first().price) / 2) &
            Q(volume__lt = 1024)
        )
    sys_ssd = sys_ssd.annotate(metrics=(F('rd_speed')) * F('volume') / pow(F('price'), 2)).order_by('-metrics')[:10]
    if random:
        selected_sys_disc = choice(sys_ssd)
    else:
        selected_sys_disc = sys_ssd.first()
    storage_options = {}
    for disctype in DiscType.objects.all():
        vol_price = {}
        volumes = Disc.objects.filter(type = disctype).order_by('volume').values_list('volume', flat=True).distinct()
        for vol in volumes:
            vol_price[vol] = round(Disc.objects.filter(type = disctype).filter(volume = vol).aggregate(Avg("price", default=0))['price__avg'] * 1024 / vol)
        storage_options[disctype.name] = vol_price
    disc_comb = find_disc_combination(storage_options, any_volume, ssd_volume, selected_mb.m2_slots - 1, selected_case.small_sata_slots, selected_case.big_sata_slots, selected_mb.sata_ports)
    types = {
        'M.2 SSD' : DiscType.objects.get(name = 'M.2 SSD'),
        '2.5" SSD' : DiscType.objects.get(name = '2.5" SSD'),
        '2.5" HDD' : DiscType.objects.get(name = '2.5" HDD'),
        '3.5" HDD' : DiscType.objects.get(name = '3.5" HDD')
    }
    disc_comb = list(map(lambda x: [types[x[0]], x[1]], disc_comb)) # !!! Появляется ошибка. Предположительно, ошибка в функции нахождения комбинаций.
    selected_discs = []
    selected_discs_obj = []
    for disc_chars in disc_comb:
        best_disc = disc_qs.filter(type = disc_chars[0]).filter(volume = disc_chars[1])
        if disc_chars[0] == types['2.5" HDD'] or disc_chars[0] == types['3.5" HDD']:
            best_disc = best_disc.order_by('price')[:10]
        else:
            if mode == 'cheap':
                best_disc.filter(price__lte = best_disc.order_by('price').first().price + (best_disc.order_by('-price').first().price - best_disc.order_by('price').first().price) / 4)
            elif mode == 'optimal':
                best_disc.filter(price__lte = best_disc.order_by('price').first().price + (best_disc.order_by('-price').first().price - best_disc.order_by('price').first().price) / 2)
            min_speed = best_disc.order_by('rd_speed').first().rd_speed
            max_speed = best_disc.order_by('-rd_speed').first().rd_speed
            min_price = best_disc.order_by('price').first().price
            max_price = best_disc.order_by('-price').first().price
            k = (max_price / min_price) / (max_speed / min_speed)
            best_disc = best_disc.annotate(metrics=(min_speed + (F('rd_speed') - min_speed) * k) / F('price')).order_by('-metrics')[:10]
        if random:
            temp = choice(best_disc)
            selected_discs.append(temp.id)
            selected_discs_obj.append(temp)
        else:
            temp = best_disc.first()
            selected_discs.append(temp.id)
            selected_discs_obj.append(temp)
    selected_discs.append(selected_sys_disc.id)
    selected_discs_obj.append(selected_sys_disc)
    combination['discs'] = selected_discs

    psu_filter = Q(typesize__in = selected_case.psu_typesize) & (Q(length = None) | Q(length__lte = selected_case.max_psu_length if selected_case.max_psu_length is not None else 1000))
    big_res = {}
    res = {}
    sides = (json.loads(selected_case.cooler_slots)).keys()
    installed = json.loads(selected_case.installed_coolers)
    for side in sides:
        if side in installed:
            res['id'] = CaseCooler.objects.get(model='Предустановленный кулер').id
            res['count'] = installed[side]['Количество']
            res['size'] = installed[side]['Размер']
            big_res[side] = res
            res = {}
        else:
            big_res[side] = {}
    current_comp = Computer(
        name = mode,
        processor = combination['processor'],
        motherboard = combination['motherboard'],
        videocard = combination['videocard'],
        memory = combination['memory'],
        memory_cnt = combination['memory_cnt'],
        case = combination['case'],
        cooler = combination['cooler'],
        casecoolers = json.dumps(big_res, sort_keys=True),
        discs = combination['discs']
    )
    min_power = calculate_psu_power(current_comp)
    psu_filter = psu_filter & Q(power__gte = min_power)
    powersupply_qs = powersupply_qs.filter(psu_filter).exclude(certificate = None)
    if mode != 'cheap' and len(powersupply_qs.filter(modular_cables = True)) > 0:
        powersupply_qs = powersupply_qs.filter(modular_cables = True)
    if mode == 'cheap':
        powersupply_qs = powersupply_qs.filter((Q(certificate = Certificate.objects.get(name = '80 PLUS Standard')) | Q(certificate = Certificate.objects.get(name = '80 PLUS Bronze')) | Q(certificate = Certificate.objects.get(name = '80 PLUS Silver'))) & Q(power__lte = min_power * 1.2))
    elif mode == 'performant':
        powersupply_qs = powersupply_qs.filter((Q(certificate = Certificate.objects.get(name = '80 PLUS Gold')) | Q(certificate = Certificate.objects.get(name = '80 PLUS Platinum')) | Q(certificate = Certificate.objects.get(name = '80 PLUS Titanium'))) & Q(power__lte = min_power * 1.5))
    else:
        powersupply_qs = powersupply_qs.filter(Q(certificate = Certificate.objects.get(name = '80 PLUS Gold')) & Q(power__lte = min_power * 1.2))
    min_power = powersupply_qs.order_by('power').first().power
    max_power = powersupply_qs.order_by('-power').first().power
    min_price = powersupply_qs.order_by('price').first().price
    max_price = powersupply_qs.order_by('-price').first().price
    k = (max_price / min_price) / (max_power / min_power)
    powersupply_qs = powersupply_qs.annotate(metrics=(min_power + (F('power') - min_power) * k) * pow(F('certificate__power_ratio'), 2) / F('price')).order_by('-metrics')
    psu_list = list(powersupply_qs)
    discs = list(map(lambda disc: disc.type.slot, selected_discs_obj))
    count = 0
    for disc in discs:
        if disc != 'M.2':
            count += 1
    psu_list = list(map(lambda psu: '__del__' if ('SATA' not in json.loads(psu.connectors).keys()) or (json.loads(psu.connectors)['SATA'] < count) or not (check_connectors(selected_gpu, selected_mb, psu)) else psu, psu_list))                                         
    while '__del__' in psu_list:
        psu_list.remove('__del__')

    if mode == 'cheap':
        while len(psu_list) > 20:
            psu_list = sorted(psu_list, key=lambda obj: obj.metrics, reverse=True)[:max(40, round(len(psu_list) / 4))]
            psu_list = sorted(psu_list, key=lambda obj: obj.power / 1000 * obj.price, reverse=True)[:max(20, round(len(psu_list) / 2))]
        psu_list = sorted(psu_list, key=lambda obj: obj.price)[:10]
    elif mode == 'optimal':
        while len(psu_list) > 20:
            psu_list = sorted(psu_list, key=lambda obj: obj.power / 1000 * obj.price, reverse=True)[:max(40, round(len(psu_list) / 3))]
            psu_list = sorted(psu_list, key=lambda obj: obj.metrics, reverse=True)[:max(20, round(len(psu_list) / 3))]
        psu_list = sorted(psu_list, key=lambda obj: obj.price)[:10]
    else:
        while len(psu_list) > 20:
            psu_list = sorted(psu_list, key=lambda obj: obj.power / 1000 * obj.price, reverse=True)[:max(40, round(len(psu_list) / 4))]
            psu_list = sorted(psu_list, key=lambda obj: obj.metrics, reverse=True)[:max(20, round(len(psu_list) / 2))]
        psu_list = sorted(psu_list, key=lambda obj: obj.power / 1000 * obj.price, reverse=True)[:10]
        psu_list = sorted(psu_list, key=lambda obj: obj.metrics, reverse=True)
    if random:
        current_comp.powersupply = choice(psu_list)
    else:
        current_comp.powersupply = psu_list[0]
    #Нет подбора корпусных кулеров !!!
    current_comp.price = sum([
        current_comp.processor.price,
        current_comp.motherboard.price,
        current_comp.videocard.price,
        current_comp.memory.price * current_comp.memory_cnt,
        current_comp.case.price,
        current_comp.cooler.price,
        sum([disc.price for disc in selected_discs_obj]),
        sum([(CaseCooler.objects.get(pk=side['id']).price * side['count'] if 'id' in side.keys() else 0) for side in json.loads(current_comp.casecoolers).values()])
    ])
    return current_comp

def main_assembler(querysets, selected_params, random = False):
    processor_qs = querysets['processor']
    videocard_qs = querysets['videocard']
    combinations = find_combinations(processor_qs, videocard_qs, random)
    cheap_global = combinations['cheap']
    optimal_global = combinations['optimal']
    performant_global = combinations['performant']
    cheap = find_necessaries(cheap_global, querysets, selected_params, 'cheap', random)
    optimal = find_necessaries(optimal_global, querysets, selected_params, 'optimal', random)
    performant = find_necessaries(performant_global, querysets, selected_params, 'performant', random)
    return cheap, optimal, performant
    
def deactivate_active(user):
    try:
        current_computer = Computer.objects.get(user=user, active=True)
        current_computer.active = False
        current_computer.save()
    except Computer.DoesNotExist:
        pass
    return

def if_none(value, replacement):
    return replacement if value is None else value
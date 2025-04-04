import json
import math
from pc_configurator.models import Disc

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
        12 : "Недостаточно коннекторов 4-pin PWM для подключения кулера и всех вентиляторов.",
        13 : "Разъём питания процессора на материнской плате отсутствует на выбранном блоке питания.",
        14 : "В корпусе недостаточно слотов расширения для установки выбранной видеокарты.",
        15 : "В корпусе недостаточно места для установки выбранной видеокарты.",
        16 : "Блок питания не имеет достаточного количества портов для питания видеокарты.",
        17 : "Кулер слишком высокий для выбранного корпуса.",
        18 : "В корпусе недостаточно места для установки всех дисков 3.5'.",
        19 : "В корпусе недостаточно места для установки всех дисков 2.5'.",
        20 : "В корпусе недостаточно места для установки всех вентиляторов.",
        21 : "Типоразмер выбранного блока питания несовместим с корпусом.",
        22 : "В корпусе недостаточно места для блока питания.",
        23 : "Блок питания не имеет достаточного числа коннекторов SATA.",
        24 : "Мощности блока питания недостаточно для питания всех комплектующих.",
    }
    return errors[index]

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

#Проверка достаточности количества коннекторов 4-pin PWM. (Код ошибки: 12)
def correct_motherboard_4pin(assembly):
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

#Проверка наличия коннектора питания процессора на блоке питания. (Код ошибки: 13)
def correct_motherboard_atx12v(assembly):
    if assembly.motherboard is not None and assembly.powersupply is not None:
        powersupply_connectors = json.loads(assembly.powersupply.connectors)
        motherboard_connectors = json.loads(assembly.motherboard.connectors)
        if (('4-pin atx-12v' in motherboard_connectors.keys() and 'CPU/4' not in powersupply_connectors.keys() and 'CPU/4+4' not in powersupply_connectors.keys()) or
            ('8-pin atx-12v' in motherboard_connectors.keys() and 'CPU/8' not in powersupply_connectors.keys() and 'CPU/4+4' not in powersupply_connectors.keys())):
            return False
        else:
            return True

#Проверка достаточности слотов расширения в корпусе. (Код ошибки: 14)
def correct_case_exp(assembly):
    if assembly.videocard is not None and assembly.case is not None:
        if assembly.case.exp_slots < assembly.videocard.exp_slots:
            return False
        else:
            return True

#Проверка максимальной длины видеокарты. (Код ошибки: 15)
def correct_case_vlen(assembly):
    if assembly.videocard is not None and assembly.case is not None:
        if assembly.case.max_gpu_length < assembly.videocard.length:
            return False
        else:
            return True

#Проверка наличия коннектора питания для видеокарты на блоке питания. (Код ошибки: 16)
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

#Проверка максимальной высоты кулера. (Код ошибки: 17)
def correct_cooler_height(assembly):
    if assembly.cooler is not None and assembly.case is not None:
        if assembly.cooler.height > assembly.case.max_cooler_height:
            return False
        else:
            return True

#Проверка достаточности количества слотов 3.5'. (Код ошибки: 18)
def correct_case_bigsata(assembly):
    if assembly.case is not None and len(assembly.discs) > 0:
        discs = count_discs_by_slot(list(map(lambda index: Disc.objects.get(pk=index), assembly.discs)))
        if 'big' in discs.keys() and assembly.case.big_sata_slots < discs['big']:
            return False
        else:
            return True

#Проверка достаточности количества слотов 2.5'. (Код ошибки: 19)
def correct_case_smallsata(assembly):
    if assembly.case is not None and len(assembly.discs) > 0:
        discs = count_discs_by_slot(list(map(lambda index: Disc.objects.get(pk=index), assembly.discs)))
        if 'small' in discs.keys() and assembly.case.small_sata_slots < discs['small']:
            return False
        else:
            return True

#Проверка достаточности места для корпусных вентиляторов. (Код ошибки: 20)
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

#Проверка совместимости блока питания с корпусом. (Код ошибки: 21)
def correct_powersupply_typesize(assembly):
    if assembly.case is not None and assembly.powersupply is not None:
        if assembly.powersupply.typesize not in assembly.case.psu_typesize:
            return False
        else:
            return True

#Проверка достаточности места для блока питания. (Код ошибки: 22)
def correct_powersupply_len(assembly):
    if assembly.case is not None and assembly.powersupply is not None:
        if assembly.case.max_psu_length is not None and assembly.powersupply.length is not None and assembly.case.max_psu_length < assembly.powersupply.length:
            return False
        else:
            return True

#Проверка достаточности коннекторов SATA у блока питания. (Код ошибки: 23)
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

#Проверка достаточности мощности блока питания. (Код ошибки: 24)
def correct_powersupply_power(assembly):
    if assembly.powersupply is not None:
        if calculate_psu_power(assembly) > assembly.powersupply.power:
            return False
        else:
            return True

#Полная проверка совместимости компонентов сборки
def check_compatibility(assembly):
    errors = []
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
    if not correct_motherboard_4pin(assembly):
        errors.append(12)
    if not correct_motherboard_atx12v(assembly):
        errors.append(13)
    if not correct_case_exp(assembly):
        errors.append(14)
    if not correct_case_vlen(assembly):
        errors.append(15)
    if not correct_videocard_connector(assembly):
        errors.append(16)
    if not correct_cooler_height(assembly):
        errors.append(17)
    if not correct_case_bigsata(assembly):
        errors.append(18)
    if not correct_case_smallsata(assembly):
        errors.append(19)
    if not correct_case_coolers(assembly):
        errors.append(20)
    if not correct_powersupply_typesize(assembly):
        errors.append(21)
    if not correct_powersupply_len(assembly):
        errors.append(22)
    if not correct_powersupply_sata(assembly):
        errors.append(23)
    if not correct_powersupply_power(assembly):
        errors.append(24)
    return [True, []] if len(errors) == 0 else [False, errors]

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
        if not buf[0]:
            return [False, buf[1]]
        else:
            return [True, []]
    else:
        return [False, []]
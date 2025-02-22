# Команда manage.py parsecomponents предназначена для добавления данных о комплектующих и их характеристиках в БД.
# Выполняется из модуля server-entrypoint.sh после миграции БД и проверки на отсутствие данных в таблицах.
# За выполнение парсинга отвечает переменная окружения INITIAL_DATA_INSERTION, при значении skip парсинг пропускается, при значении exec - выполняется.

from django.core.management.base import BaseCommand
from django.core.exceptions import ObjectDoesNotExist
from pc_configurator.models import Manufacturer, Processor, Motherboard, Videocard, Memory, Cooler, Case, Disc, CaseCooler, PowerSupply, DiscType, Certificate
from dotenv import load_dotenv
import os
from selenium import webdriver
from bs4 import BeautifulSoup
import requests
import time
import json
import math
from colorama import Fore

SLEEP_WHILE_LOADING = 5 # Время ожидания загрузки страницы

# Функция возвращает словарь, в котором каждому компоненту соответствует его рейтинг производительности.
def get_component_rates(component_type: str):
    rates = {}
    cpu_arr = []
    rate_arr = []
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.104 Safari/537.36"
    }
    sourcecode = ""
    if component_type == "cpu_high_end" or component_type == "cpu_mid_range" or component_type == "cpu_low_range":
        while sourcecode == "":
            try:
                if component_type == "cpu_high_end":
                    sourcecode = requests.get('https://www.cpubenchmark.net/high_end_cpus.html', headers = headers, timeout=10).text
                elif component_type == "cpu_mid_range":
                    sourcecode = requests.get('https://www.cpubenchmark.net/mid_range_cpus.html', headers = headers, timeout=10).text
                else:
                    sourcecode = requests.get('https://www.cpubenchmark.net/midlow_range_cpus.html', headers = headers, timeout=10).text
            except requests.exceptions.Timeout:
                print(Fore.RED + "Connection time out. Trying again...")
                time.sleep(3)
            except requests.exceptions.ConnectionError:
                print(Fore.RED + "Connection have not been established. Trying again...")
                time.sleep(3)
        soup = BeautifulSoup(sourcecode, 'html.parser')
    elif component_type == "gpu":
        while sourcecode == "":
            try:
                sourcecode = requests.get('https://www.videocardbenchmark.net/high_end_gpus.html', headers = headers, timeout=10).text
            except requests.exceptions.Timeout:
                print(Fore.RED + "Connection time out. Trying again...")
                time.sleep(3)
            except requests.exceptions.ConnectionError:
                print(Fore.RED + "Connection have not been established. Trying again...")
                time.sleep(3)
        soup = BeautifulSoup(sourcecode, 'html.parser')
    else:
        raise ValueError('Wrong component type!')
    soup = soup.select('#mark > div:nth-child(1) > div:nth-child(3) > ul:nth-child(1) > li > a')
    for comp in soup:
        model = comp.find('span', class_='prdname').contents[0].split(" @")[0]
        rate = int("".join(comp.find('span', class_='count').contents[0].split(",")))
        rates[model] = rate
    return rates

# Функция, объединяющая элементы массива типа массива [[ , ], [ , ]] в единый массив [ , , , ]
def merge_lists(ilist):
    out = []
    for i in range(len(ilist)):
        for j in range(len(ilist[i])):
            out.append(ilist[i][j])
    return out

class Api:
    def __init__(self, url: str):
        self.url = url
        high = get_component_rates('cpu_high_end')
        time.sleep(3)
        mid = get_component_rates('cpu_mid_range')
        time.sleep(3)
        low = get_component_rates('cpu_low_range')
        self.cpu_rates = {**high, **mid, **low}
        if len(self.cpu_rates) > 0:
            print(Fore.CYAN + 'CPU rates parsed successfully.')
        else:
            print(Fore.RED + 'Error occured while parsing CPU rates.')
        self.gpu_rates = get_component_rates('gpu')
        if len(self.gpu_rates) > 0:
            print(Fore.CYAN + 'GPU rates parsed successfully.')
        else:
            print(Fore.RED + 'Error occured while parsing GPU rates.')

    # Функция, возвращающая исходный код страницы по передаваемой ссылке
    def get_source_code(self, path: str):
        user_agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.104 Safari/537.36'
        chrome_options = webdriver.ChromeOptions()
        chrome_options.add_argument(f'user-agent={user_agent}')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--window-size=1920,1080')
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--disable-blink-features=AutomationControlled')
        chrome_options.add_argument('--allow-running-insecure-content')
        #chrome_options.add_argument('--disable-dev-shm-usage') # Аргумент запрещает использовать буфер ОП для выгрузки страницы, вместо этого используется /tmp на диске.
        driver = webdriver.Chrome(options=chrome_options)
        driver.get(path)
        time.sleep(SLEEP_WHILE_LOADING)
        html_source = driver.page_source
        driver.close()
        return html_source

    # Функция, возвращающая количество страниц компонентов
    def get_pages_count(self, path: str):
        soup = BeautifulSoup(self.get_source_code(self.url + path), 'html.parser')
        return int(soup.select('li.PaginationBody_item__ztWtW:nth-child(5) > a:nth-child(1)')[0].contents[0])

    # Функция, возвращающая массив собранных со страницы ссылок на компоненты
    def get_component_links(self, path: str):
        hrefs = []
        soup = BeautifulSoup(self.get_source_code(self.url + path), 'html.parser')
        for a in soup.select('div.Card_wrap__hES44:nth-child(n) > div:nth-child(1) > div:nth-child(2) > div:nth-child(1) > div:nth-child(2) > a:nth-child(1)'):
                hrefs.append(self.url + a['href'])
        return hrefs

    # Функция, возвращающая массив всех ссылок на компоненты одного типа
    def collect_component_links(self, component_path: str, qfilter: str):
        links =[]
        pages_count = self.get_pages_count(component_path + '?q=' + qfilter) if len(qfilter) > 0 else self.get_pages_count(component_path)
        base_links = [component_path + '?page=' + str(num+1) for num in range(pages_count)]
        if len(qfilter) > 0:
            base_links = list(map(lambda x: x + '&q=' + qfilter, base_links))
        for link in base_links:
            links.append(self.get_component_links(link))
        return merge_lists(links)

    # Функция, возвращающая рейтинг производительности компонента (процессоров и видеокарт)
    def get_rate_by_model(self, component_type: str, rates: dict, component: dict):
        if component_type == "cpu":
            for model in list(rates.keys()):
                if component['manufacturer'] in model and component['series'] in model and component['model'] in model:
                    return rates.get(model)
        elif component_type == "gpu":
            for model in list(rates.keys()):
                if component['chip'] in model:
                    return rates.get(model)
        else:
            raise ValueError('Wrong component type!')
        
    # Функция, возвращающая всю собираемую о компоненте информацию в виде списка, обрабатывая поля типа string, boolean, integer
    def get_component_info(self, url: str, valid_keys: dict, string_fields: list, integer_fields: list, boolean_fields: list):
        keys = []
        values = []
        lst = {}
        soup = BeautifulSoup(self.get_source_code(url), 'html.parser')
        for a in soup.select('div.ProductCharacteristics_column__CtrZL:nth-child(n) > section:nth-child(n) > div:nth-child(2) > div:nth-child(1) > div:nth-child(1) > div:nth-child(n) > div:nth-child(1) > div:nth-child(1) > span:nth-child(1)'):
                keys.append(a.text)
        for a in soup.select('div.ProductCharacteristics_column__CtrZL:nth-child(n) > section:nth-child(n) > div:nth-child(2) > div:nth-child(1) > div:nth-child(1) > div:nth-child(n) > div:nth-child(2) > div:nth-child(1)'):
                values.append(a.text)
        values = list(map(lambda x: x.replace('\xa0', ' ').split()[0] if '\xa0' in x else x, values))
        keys = list(map(lambda x: '__del__' if x not in list(valid_keys.keys()) else x, keys))
        while '__del__' in keys:
            place = keys.index('__del__')
            keys.pop(place)
            values.pop(place)
        keys = list(map(lambda x: valid_keys.get(x), keys))
        for i in range(len(keys)):
            if keys[i] in string_fields:
                lst[keys[i]] = values[i]
            elif keys[i] in integer_fields:
                lst[keys[i]] = int(values[i])
            elif keys[i] in boolean_fields:
                lst[keys[i]] = True if values[i] == 'да' else False
            else:
                lst[keys[i]] = values[i]
        try:
            lst['price'] = int(soup.select('.PriceBlock_price__j_PbO > span:nth-child(1)')[0].text.replace('\xa0', '').replace('RUB', '').replace(',', ''))
        except IndexError:
            lst['price'] = 0
        lst['link'] = url
        return lst

    def cooler_mapping(self, sizes: list):
        lst = list(map(lambda x: int(x), sizes))
        if len(lst) > 2:
            maximum = 0
            for i in range(0, len(lst)-1, 2):
                if lst[i]*lst[i + 1] > maximum:
                    size = lst[i + 1]
                    count = lst[i]
                    maximum = size*count
            return {'Размер' : size, 'Количество' : count}
        elif len(lst) == 1:
            return {'Размер' : lst[0], 'Количество' : 1}
        elif lst[0] > 8:
            return {'Размер' : max(lst), 'Количество' : 1}
        else:
            return {'Размер' : lst[1], 'Количество' : lst[0]}


    def get_component_info_case_extension(self, url: str, valid_keys: dict, string_fields: list, integer_fields: list, boolean_fields: list):
        keys = []
        values = []
        lst = {}
        soup = BeautifulSoup(self.get_source_code(url), 'html.parser')
        for a in soup.select('div.ProductCharacteristics_column__CtrZL:nth-child(n) > section:nth-child(n) > div:nth-child(2) > div:nth-child(1) > div:nth-child(1) > div:nth-child(n) > div:nth-child(1) > div:nth-child(1) > span:nth-child(1)'):
                keys.append(a.text)
        for a in soup.select('div.ProductCharacteristics_column__CtrZL:nth-child(n) > section:nth-child(n) > div:nth-child(2) > div:nth-child(1) > div:nth-child(1) > div:nth-child(n) > div:nth-child(2) > div:nth-child(1)'):
                values.append(a.text)
        values = list(map(lambda x: x.replace('\xa0', ' ').split()[0] if '\xa0' in x else x, values))
        keys = list(map(lambda x: '__del__' if x not in list(valid_keys.keys()) else x, keys))
        while '__del__' in keys:
            place = keys.index('__del__')
            keys.pop(place)
            values.pop(place)
        keys = list(map(lambda x: valid_keys.get(x), keys))
        for i in range(len(keys)):
            if keys[i] in string_fields:
                lst[keys[i]] = values[i]
            elif keys[i] in integer_fields:
                lst[keys[i]] = int(values[i])
            elif keys[i] in boolean_fields:
                lst[keys[i]] = True if values[i] == 'да' else False
            else:
                lst[keys[i]] = values[i]
        try:
            lst['price'] = int(soup.select('.PriceBlock_price__j_PbO > span:nth-child(1)')[0].text.replace('\xa0', '').replace('RUB', '').replace(',', ''))
        except IndexError:
            lst['price'] = 0
        lst['link'] = url
        allowed_keys = ['Передняя панель', 'Задняя панель', 'Нижняя панель', 'Верхняя панель', 'Боковая панель']
        mounted = {}
        expanded = {}
        mount = False
        expand = False
        cooler_slots_exist = []
        coolers_mounted = []
        headers = list(map(lambda x: x.text, soup.select('div.ProductCharacteristics_column__CtrZL:nth-child(1) > section:nth-child(n) > h3:nth-child(1)')))
        if 'Места для дополнительных вентиляторов' in headers:
            cooler_slots_exist = [1, headers.index('Места для дополнительных вентиляторов') + 1]
        if 'Установленные вентиляторы' in headers:
            coolers_mounted = [1, headers.index('Установленные вентиляторы') + 1]
        if len(coolers_mounted) == 0 or len(cooler_slots_exist) == 0:
            headers = list(map(lambda x: x.text, soup.select('div.ProductCharacteristics_column__CtrZL:nth-child(2) > section:nth-child(n) > h3:nth-child(1)')))
            if 'Места для дополнительных вентиляторов' in headers:
                cooler_slots_exist = [2, headers.index('Места для дополнительных вентиляторов') + 1]
            if 'Установленные вентиляторы' in headers:
                coolers_mounted = [2, headers.index('Установленные вентиляторы') + 1]
        if len(cooler_slots_exist) > 0:
            expanded_keys = list(map(lambda x: x.text, soup.select(f'div.ProductCharacteristics_column__CtrZL:nth-child({cooler_slots_exist[0]}) > section:nth-child({cooler_slots_exist[1]}) > div:nth-child(2) > div:nth-child(1) > div:nth-child(1) > div:nth-child(n) > div:nth-child(1) > div:nth-child(1) > span:nth-child(1)')))
            expanded_keys.pop(0)
            expanded_values = list(map(lambda x: x.text.replace(' мм', '').replace(' или ', ' x ').split(' x '), soup.select(f'div.ProductCharacteristics_column__CtrZL:nth-child({cooler_slots_exist[0]}) > section:nth-child({cooler_slots_exist[1]}) > div:nth-child(2) > div:nth-child(1) > div:nth-child(1) > div:nth-child(n) > div:nth-child(2) > div:nth-child(1) > span:nth-child(1)')))
            expanded_values.pop(0)
            expanded_keys = list(map(lambda x: '__del__' if x not in allowed_keys else x, expanded_keys))
            while '__del__' in expanded_keys:
                ind = expanded_keys.index('__del__')
                expanded_keys.pop(ind)
                expanded_values.pop(ind)
        if len(coolers_mounted) > 0:
            mounted_keys = list(map(lambda x: x.text, soup.select(f'div.ProductCharacteristics_column__CtrZL:nth-child({coolers_mounted[0]}) > section:nth-child({coolers_mounted[1]}) > div:nth-child(2) > div:nth-child(1) > div:nth-child(1) > div:nth-child(n) > div:nth-child(1) > div:nth-child(1) > span:nth-child(1)')))
            mounted_keys.pop(0)
            mounted_values = list(map(lambda x: x.text.replace(' мм', '').replace(' или ', ' x ').split(' x '), soup.select(f'div.ProductCharacteristics_column__CtrZL:nth-child({coolers_mounted[0]}) > section:nth-child({coolers_mounted[1]}) > div:nth-child(2) > div:nth-child(1) > div:nth-child(1) > div:nth-child(n) > div:nth-child(2) > div:nth-child(1) > span:nth-child(1)')))
            mounted_values.pop(0)
            mounted_keys = list(map(lambda x: '__del__' if x not in allowed_keys else x, mounted_keys))
            while '__del__' in mounted_keys:
                ind = mounted_keys.index('__del__')
                mounted_keys.pop(ind)
                mounted_values.pop(ind)
            for key in mounted_keys:
                if key not in expanded_keys:
                    ind = mounted_keys.index(key)
                    expanded_keys.append(key)
                    expanded_values.append(mounted_values[ind])

        if len(cooler_slots_exist) > 0:
            expanded_values = list(map(self.cooler_mapping, expanded_values))
            for i in range(len(expanded_keys)):
                expanded[expanded_keys[i]] = expanded_values[i]
        if len(coolers_mounted) > 0:
            mounted_values = list(map(self.cooler_mapping, mounted_values))
            for i in range(len(mounted_keys)):
                mounted[mounted_keys[i]] = mounted_values[i]
        lst['cooler_slots'] = json.dumps(expanded, sort_keys=True)
        lst['installed_coolers'] = json.dumps(mounted, sort_keys=True)
        return lst

    # Функция, формирующая из строки список портов в заданном формате
    def collect_ports(self, ports: str):
        pports = list(map(lambda x: x.split(' x '), ports.split(', ')) )
        lst = {}
        for port in pports:
            if len(port) > 1:
                lst[port[1]] = int(port[0])
            else:
                lst[port[0]] = 1
        return lst

    def get_processor_info(self, url: str):
        valid_keys = {
            'Производитель' : 'manufacturer',
            'Линейка' : 'series',
            'Модель' : 'model',
            'Socket' : 'socket',
            'Количество ядер' : 'cores',
            'Высокопроизводительные ядра' : 'p_cores',
            'Энергоэффективные ядра' : 'e_cores',
            'Количество потоков' : 'threads',
            'Тактовая частота' : 'frequency',
            'Частота процессора в режиме Turbo' : 'turbo_freq',
            'Разблокированный множитель' : 'unlocked',
            'Интегрированное графическое ядро' : 'int_graphics',
            'Типичное тепловыделение' : 'tdp'
        }
        string_fields = ['manufacturer', 'series', 'model', 'socket']
        integer_fields = ['cores', 'p_cores', 'e_cores', 'threads', 'frequency', 'turbo_freq', 'tdp']
        boolean_fields = ['unlocked', 'int_graphics']
        processor = self.get_component_info(url, valid_keys, string_fields, integer_fields, boolean_fields)
        if 'p_cores' not in list(processor.keys()) or 'e_cores' not in list(processor.keys()):
            processor['p_cores'] = processor['cores']
            processor['e_cores'] = 0
        if 'unlocked' not in list(processor.keys()):
            processor['unlocked'] = False
        if 'int_graphics' not in list(processor.keys()):
            processor['int_graphics'] = False
        if 'threads' not in list(processor.keys()):
            processor['threads'] = processor['cores']
        rate = self.get_rate_by_model('cpu', self.cpu_rates, processor)
        if rate != None:
            processor['rate'] = rate
            return processor
        else:
            return {}

    def get_motherboard_info(self, url: str):
        valid_keys = {
            'Производитель' : 'manufacturer',
            'Код производителя' : 'model',
            'Socket' : 'socket',
            'Чипсет' : 'PROCESS_chipset',
            'Форм-фактор' : 'formfactor',
            'Тип памяти' : 'PROCESS_mem_type',
            'Количество слотов памяти' : 'mem_slots',
            'Версия Wi-Fi' : 'wifi_ver',
            'Версия Bluetooth' : 'bluetooth_ver',
            'Контроллер SATA' : 'PROCESS_sata_ports',
            'Разъёмы на задней панели' : 'PROCESS_backports',
            'Слоты расширения' : 'PROCESS_exp',
            'Разъёмы для подключения вентиляторов корпуса' : 'PROCESS_casecool',
            'Разъём питания ATX 12 В' : 'PROCESS_cpupower',
            'Разъём питания PCIe' : 'PROCESS_pciepower',
            'Внутренние порты USB на плате' : 'PROCESS_internal_usb',
            'Коннекторы ARGB 5V на плате' : 'PROCESS_leds5',
            'Коннекторы RGB 12V на плате' : 'PROCESS_leds12',
        }
        string_fields = ['manufacturer', 'model', 'socket', 'formfactor', 'wifi_ver', 'bluetooth_ver']
        integer_fields = ['mem_slots']
        boolean_fields = []
        motherboard = self.get_component_info(url, valid_keys, string_fields, integer_fields, boolean_fields)
        motherboard['mem_type'] = motherboard['PROCESS_mem_type'].split(', ')[0]
        del motherboard['PROCESS_mem_type']
        try:
            motherboard['chipset'] = motherboard['PROCESS_chipset'].split()[1]
            del motherboard['PROCESS_chipset']
        except KeyError:
            return {}
        try:
            motherboard['sata_ports'] = int(motherboard['PROCESS_sata_ports'].split()[0])
            del motherboard['PROCESS_sata_ports']
        except ValueError:
            motherboard['sata_ports'] = 1
        motherboard['backports'] = json.dumps(self.collect_ports(motherboard['PROCESS_backports']), sort_keys=True)
        del motherboard['PROCESS_backports']
        if 'PROCESS_internal_usb' in list(motherboard.keys()):
            motherboard['internal_usb'] = json.dumps(self.collect_ports(motherboard['PROCESS_internal_usb']), sort_keys=True)
            del motherboard['PROCESS_internal_usb']
        ports = list(map(lambda x: x.split(' x '), motherboard['PROCESS_exp'].split(', ')) )
        cnt = 0
        max_ver = 0.0
        pciex1_slots = 0
        m2_slots = 0
        for port in ports:
            if len(port) > 1:
                if 'M.2' in port[1]:
                    m2_slots = int(port[0])
                elif 'x16' in port[1]:
                    cnt += int(port[0])
                    try:
                        max_ver = float(port[1].split()[1]) if max_ver < float(port[1].split()[1]) else max_ver
                    except ValueError:
                        pass
                elif 'x1' in port[1]:
                    pciex1_slots = int(port[0])
                else:
                    pass
            else:
                if 'M.2' in port[0]:
                    m2_slots = 1
                elif 'x16' in port[0]:
                    cnt += 1
                    try:
                        max_ver = float(port[0].split()[1]) if max_ver < float(port[0].split()[1]) else max_ver
                    except ValueError:
                        pass
                elif 'x1' in port[0]:
                    pciex1_slots = 1
                else:
                    pass
        motherboard['pciex16_slots'] = cnt
        motherboard['pciex16_ver'] = max_ver
        motherboard['m2_slots'] = m2_slots
        motherboard['pciex1_slots'] = pciex1_slots
        del motherboard['PROCESS_exp']
        arr = []
        if 'PROCESS_casecool' in list(motherboard.keys()):
            listing = list(map(lambda x: x.split(' x '), motherboard['PROCESS_casecool'].split(', ')))[0]
            if len(listing) > 1:
                listing[0] = int(listing[0])
                listing[1] += ' pwm'
            else:
                listing[0] += ' pwm'
                listing.insert(0, 1)
            arr.append(listing)
            del motherboard['PROCESS_casecool']
        if 'PROCESS_cpupower' in list(motherboard.keys()):
            listing = list(map(lambda x: x.split(' x '), motherboard['PROCESS_cpupower'].split(', ')))[0]
            if len(listing) > 1:
                listing[0] = int(listing[0])
                listing[1] += ' atx-12v'
            else:
                listing[0] += ' atx-12v'
                listing.insert(0, 1)
            arr.append(listing)
            del motherboard['PROCESS_cpupower']
        if 'PROCESS_pciepower' in list(motherboard.keys()):
            listing = list(map(lambda x: x.split(' x '), motherboard['PROCESS_pciepower'].split(', ')))[0]
            if len(listing) > 1:
                listing[0] = int(listing[0])
                listing[1] += ' pcie'
            else:
                listing[0] += ' pcie'
                listing.insert(0, 1)
            arr.append(listing)
            del motherboard['PROCESS_pciepower']
        if 'PROCESS_leds5' in list(motherboard.keys()):
            listing = list(map(lambda x: x.split(' x '), motherboard['PROCESS_leds5'].split(', ')))[0]
            if len(listing) > 1:
                listing[0] = int(listing[0])
                listing[1] += ' argb-5v'
            else:
                listing[0] += ' argb-5v'
                listing.insert(0, 1)
            arr.append(listing)
            del motherboard['PROCESS_leds5']
        if 'PROCESS_leds12' in list(motherboard.keys()):
            listing = list(map(lambda x: x.split(' x '), motherboard['PROCESS_leds12'].split(', ')))[0]
            if len(listing) > 1:
                listing[0] = int(listing[0])
                listing[1] += ' rgb-12v'
            else:
                listing[0] += ' rgb-12v'
                listing.insert(0, 1)
            arr.append(listing)
            del motherboard['PROCESS_leds12']
        lst = {}
        for port in arr:
            lst[port[1]] = port[0]
        motherboard['connectors'] = json.dumps(lst, sort_keys=True)
        return motherboard

    def get_videocard_info(self, url: str):
        valid_keys = {

            'Производитель' : 'manufacturer',
            'Код производителя' : 'model',
            'Серия' : 'chip',
            'Производитель видеопроцессора' : 'chip_manufacturer',
            'Интерфейс' : 'PROCESS_pciex16_ver',
            'Тип памяти' : 'PROCESS_mem_type',
            'Количество вентиляторов' : 'PROCESS_coolers',
            'Разъёмы' : 'PROCESS_backports',
            'Частота графического процессора' : 'PROCESS_frequency',
            'Частота графического процессора (Boost)' : 'PROCESS_boost_freq',
            'Объём памяти' : 'PROCESS_mem_volume',
            'Шина памяти (разрядность)' : 'PROCESS_bus_width',
            'Пропускная способность' : 'PROCESS_bandwidth',
            'Количество поддерживаемых мониторов' : 'max_monitors',
            'Разъём дополнительного питания' : 'PROCESS_power_pins',
            'Рекомендуемая мощность блока питания' : 'PROCESS_psu_power',
            'Количество занимаемых слотов' : 'PROCESS_exp_slots',
            'Длина' : 'PROCESS_length'    
        }
        string_fields = ['manufacturer', 'model', 'chip', 'chip_manufacturer']
        integer_fields = ['max_monitors']
        boolean_fields = []
        videocard = self.get_component_info(url, valid_keys, string_fields, integer_fields, boolean_fields)
        videocard['chip'] = videocard['chip'].replace('Super', 'SUPER')
        try:
            videocard['mem_type'] = videocard['PROCESS_mem_type'].split(', ')[0]
            del videocard['PROCESS_mem_type']
        except KeyError:
            return {}
        try:
            videocard['pciex16_ver'] = float(videocard['PROCESS_pciex16_ver'].split()[2])
            del videocard['PROCESS_pciex16_ver']
        except KeyError:
            return {}
        videocard['frequency'] = int(videocard['PROCESS_frequency'].split()[0])
        del videocard['PROCESS_frequency']
        try:
            videocard['boost_freq'] = int(videocard['PROCESS_boost_freq'].split()[0])
            del videocard['PROCESS_boost_freq']
        except KeyError:
            pass
        videocard['mem_volume'] = int(videocard['PROCESS_mem_volume'].split()[0])
        del videocard['PROCESS_mem_volume']
        videocard['bus_width'] = int(videocard['PROCESS_bus_width'].split()[0])
        del videocard['PROCESS_bus_width']
        try:
            videocard['coolers'] = int(videocard['PROCESS_coolers'].split(',')[0])
            del videocard['PROCESS_coolers']
        except KeyError:
            pass
        try:
            videocard['bandwidth'] = round(float(videocard['PROCESS_bandwidth'].split()[0]))
            del videocard['PROCESS_bandwidth']
        except KeyError:
            pass
        videocard['backports'] = json.dumps(self.collect_ports(videocard['PROCESS_backports']), sort_keys=True)
        del videocard['PROCESS_backports']
        try:
            connectors = list(map(lambda x: x.replace(' ', '-'), videocard['PROCESS_power_pins'].split(', ')[0].split(' + ')))
            lst = {}
            for connector in connectors:
                if connector not in list(lst.keys()):
                    lst[connector] = 1
                else:
                    lst[connector] += 1
            videocard['power_pins'] = json.dumps(lst, sort_keys=True)
            del videocard['PROCESS_power_pins']
        except KeyError:
            pass
        try:
            videocard['psu_power'] = int(videocard['PROCESS_psu_power'].split()[0])
            del videocard['PROCESS_psu_power']
        except KeyError:
            return {}
        try:
            videocard['length'] = round(float(videocard['PROCESS_length'].split()[0]))
            del videocard['PROCESS_length']
        except KeyError:
            return {}
        videocard['exp_slots'] = math.floor(float(videocard['PROCESS_exp_slots']))
        del videocard['PROCESS_exp_slots']
        rate = self.get_rate_by_model('gpu', self.gpu_rates, videocard)
        if rate != None:
            videocard['rate'] = rate
            return videocard
        else:
            return {}

    def get_case_info(self, url: str):
        valid_keys = {
            'Производитель' : 'manufacturer',
            'Код производителя' : 'model',
            'Типоразмер' : 'typesize',
            'Форм-фактор' : 'PROCESS_mb_ffs',
            'Форм-фактор БП' : 'PROCESS_psu_typesize',
            'Внутренние отсеки 3.5"' : 'PROCESS_big_sata_slots',
            'Внутренние отсеки 2.5"' : 'PROCESS_small_sata_slots',
            'Максимальная длина видеокарты' : 'PROCESS_max_gpu_length',
            'Максимальная высота кулера' : 'PROCESS_max_cooler_height',
            'Максимальная длина БП' : 'PROCESS_max_psu_length',
            'Интерфейсы на лицевой панели' : 'PROCESS_front_interfaces',
            'Количество слотов расширения' : 'PROCESS_exp_slots',
            'Возможность установки СЖО' : 'liquid_possible',
            'Размеры (ШхВхГ)' : 'PROCESS_size',
            'Вес' : 'PROCESS_mass'
        }
        string_fields = ['manufacturer', 'typesize', 'model']
        integer_fields = []
        boolean_fields = ['liquid_possible']
        case = self.get_component_info_case_extension(url, valid_keys, string_fields, integer_fields, boolean_fields)
        if 'model' not in case.keys():
            return {}
        try:
            case['psu_typesize'] = case['PROCESS_psu_typesize'].split(', ')
            del case['PROCESS_psu_typesize']
        except:
            return {}
        try:
            case['exp_slots'] = int(case['PROCESS_exp_slots'].split(', ')[0])
            del case['PROCESS_exp_slots']
        except:
            case['exp_slots'] = 0
        try:
            case['big_sata_slots'] = int(case['PROCESS_big_sata_slots'].split(', ')[0])
            del case['PROCESS_big_sata_slots']
        except KeyError:
            case['big_sata_slots'] = 0
        try:
            case['small_sata_slots'] = int(case['PROCESS_small_sata_slots'].split(', ')[0])
            del case['PROCESS_small_sata_slots']
        except KeyError:
            case['small_sata_slots'] = 0
        try:
            case['max_gpu_length'] = math.floor(float(case['PROCESS_max_gpu_length']))
            del case['PROCESS_max_gpu_length']
        except KeyError:
            return {}
        try:
            case['max_cooler_height'] = math.floor(float(case['PROCESS_max_cooler_height']))
            del case['PROCESS_max_cooler_height']
        except KeyError:
            return {}
        try:
            case['max_psu_length'] = math.floor(float(case['PROCESS_max_psu_length']))
            del case['PROCESS_max_psu_length']
        except KeyError:
            pass
        try:
            case['mb_ffs'] = case['PROCESS_mb_ffs'].split(', ')
            del case['PROCESS_mb_ffs']
        except KeyError:
            return {}
        try:
            case['front_interfaces'] = json.dumps(self.collect_ports(case['PROCESS_front_interfaces']), sort_keys=True)
            del case['PROCESS_front_interfaces']
        except KeyError:
            pass
        try:
            case['mass'] = (case['PROCESS_mass'].split()[0])
            del case['PROCESS_mass']
        except KeyError:
            pass
        try:
            sizes = case['PROCESS_size'].replace(' мм', '').split(' x ')
            case['height'] = round(float(sizes[1]))
            case['width'] = round(float(sizes[0]))
            case['length'] = round(float(sizes[2]))
            del case['PROCESS_size']
        except KeyError:
            pass
        return case

    def get_powersupply_info(self, url: str):
        valid_keys = {
            'Производитель' : 'manufacturer',
            'Код производителя' : 'model',
            'Мощность' : 'PROCESS_power',
            'PFC' : 'PROCESS_pfc_act',
            'Стандарт' : 'PROCESS_typesize',
            'Сертификат 80 PLUS' : 'PROCESS_certificate',
            'Отстёгивающиеся кабели' : 'modular_cables',
            'Размеры (ШхВхГ)' : 'PROCESS_size',
            'Тип разъёма для материнской платы' : 'PROCESS_mb_connector',
            'Количество разъёмов 4-pin CPU' : 'PROCESS_cpu_4p',
            'Количество разъёмов 4+4-pin CPU' : 'PROCESS_cpu_4+4p',
            'Количество разъёмов 8-pin CPU' : 'PROCESS_cpu_8p',
            'Количество разъёмов 6-pin PCI-E' : 'PROCESS_gpu_6p',
            'Количество разъёмов 6+2-pin PCI-E' : 'PROCESS_gpu_6+2p',
            'Количество разъёмов 8-pin PCI-E' : 'PROCESS_gpu_8p',
            'Количество разъёмов 12+4-pin PCI-E 5.0 (12VHPWR)' : 'PROCESS_gpu_12+4p_12VHPWR',
            'Количество разъёмов 12+4-pin PCI-E 5.1 (12-2x6)' : 'PROCESS_gpu_12+4p_12-2x6',
            'Количество разъёмов 4-pin IDE (Molex)' : 'PROCESS_molex',
            'Количество разъёмов 15-pin SATA' : 'PROCESS_sata',
            'Количество разъёмов 4-pin Floppy' : 'PROCESS_floppy'
            }
        string_fields = ['manufacturer', 'model']
        integer_fields = []
        boolean_fields = ['modular_cables']
        psu = self.get_component_info(url, valid_keys, string_fields, integer_fields, boolean_fields)
        if 'model' not in psu.keys():
            return {}
        try:
            psu['power'] = int(psu['PROCESS_power'].split()[0])
            del psu['PROCESS_power']
        except:
            return {}
        try:
            if psu['PROCESS_certificate'] == 'нет':
                pass
            else:
                psu['certificate'] = psu['PROCESS_certificate']
            del psu['PROCESS_certificate']
        except KeyError:
            pass
        try:
            psu['pfc_act'] = True if psu['PROCESS_pfc_act'] == 'активный' else False
            del psu['PROCESS_pfc_act']
        except KeyError:
            psu['pfc_act'] = False
        try:
            psu['typesize'] = psu['PROCESS_typesize'].split('12V')[0]
            del psu['PROCESS_typesize']
        except KeyError:
            return {}
        try:
            psu['length'] = math.ceil(float(psu['PROCESS_size'].replace(' мм', '').split(' x ')[2]))
            del psu['PROCESS_size']
        except KeyError:
            pass
        lst = {}
        try:
            lst['MB'] = psu['PROCESS_mb_connector'].split()[0]
            del psu['PROCESS_mb_connector']
        except KeyError:
            return {}
        try:
            lst['CPU/4'] = int(psu['PROCESS_cpu_4p'])
            del psu['PROCESS_cpu_4p']
        except KeyError:
            pass
        try:
            lst['CPU/4+4'] = int(psu['PROCESS_cpu_4+4p'])
            del psu['PROCESS_cpu_4+4p']
        except KeyError:
            pass
        try:
            lst['CPU/8'] = int(psu['PROCESS_cpu_8p'])
            del psu['PROCESS_cpu_8p']
        except KeyError:
            pass
        try:
            lst['GPU/6'] = int(psu['PROCESS_gpu_6p'])
            del psu['PROCESS_gpu_6p']
        except KeyError:
            pass
        try:
            lst['GPU/6+2'] = int(psu['PROCESS_gpu_6+2p'])
            del psu['PROCESS_gpu_6+2p']
        except KeyError:
            pass
        try:
            lst['GPU/8'] = int(psu['PROCESS_gpu_8p'])
            del psu['PROCESS_gpu_8p']
        except KeyError:
            pass
        try:
            lst['GPU/12+4/12VHPWR'] = int(psu['PROCESS_gpu_12+4p_12VHPWR'])
            del psu['PROCESS_gpu_12+4p_12VHPWR']
        except KeyError:
            pass
        try:
            lst['GPU/12+4/12-2x6'] = int(psu['PROCESS_gpu_12+4p_12-2x6'])
            del psu['PROCESS_gpu_12+4p_12-2x6']
        except KeyError:
            pass
        try:
            lst['MOLEX'] = int(psu['PROCESS_molex'].split(',')[0])
            del psu['PROCESS_molex']
        except KeyError:
            pass
        try:
            lst['SATA'] = int(psu['PROCESS_sata'])
            del psu['PROCESS_sata']
        except KeyError:
            pass
        try:
            lst['FLOPPY'] = int(psu['PROCESS_floppy'])
            del psu['PROCESS_floppy']
        except KeyError:
            pass
        psu['connectors'] = json.dumps(lst, sort_keys=True)
        return psu

    def get_memory_info(self, url: str):
        valid_keys = {
            'Производитель' : 'manufacturer',
            'Код производителя' : 'model',
            'Объём одного модуля' : 'PROCESS_volume',
            'Тип памяти' : 'mem_type',
            'Тактовая частота' : 'PROCESS_frequency',
            'Пропускная способность' : 'PROCESS_bandwidth',
            'CAS Latency (CL)' : 'latency'
        }
        string_fields = ['manufacturer', 'model', 'mem_type']
        integer_fields = ['latency']
        boolean_fields = []
        memory = self.get_component_info(url, valid_keys, string_fields, integer_fields, boolean_fields)
        if 'model' not in memory.keys():
            return {}
        if 'mem_type' not in memory.keys():
            return {}
        if 'latency' not in memory.keys():
            return {}
        try:
            memory['volume'] = int(memory['PROCESS_volume'].split()[0])
            del memory['PROCESS_volume']
        except KeyError:
            return {}
        try:
            memory['frequency'] = int(memory['PROCESS_frequency'].split()[0])
            del memory['PROCESS_frequency']
        except KeyError:
            return {}
        try:
            memory['bandwidth'] = int(memory['PROCESS_bandwidth'].split()[0])
            del memory['PROCESS_bandwidth']
        except KeyError:
            return {}
        return memory

    def get_air_cooler_info(self, url: str):
        valid_keys = {
            'Производитель' : 'manufacturer',
            'Код производителя' : 'model',
            'Socket' : 'PROCESS_sockets',
            'Максимальная рассеиваемая мощность' : 'PROCESS_power',
            'Высота кулера' : 'PROCESS_height',
            'Уровень шума вентилятора' : 'PROCESS_noise_level'
        }
        string_fields = ['manufacturer', 'model']
        integer_fields = []
        boolean_fields = []
        air_cooler = self.get_component_info(url, valid_keys, string_fields, integer_fields, boolean_fields)
        if 'model' not in air_cooler.keys():
            return {}
        try:
            air_cooler['sockets'] = air_cooler['PROCESS_sockets'].replace('LGA 115x/1200', 'LGA 1150, LGA 1151, LGA 1155, LGA 1156, LGA 1200').replace('1851', 'LGA 1851').replace('2011-3', 'LGA 2011-3').split(', ')
            del air_cooler['PROCESS_sockets']
        except KeyError:
            return {}
        try:
            air_cooler['power'] = int(air_cooler['PROCESS_power'].split()[0])
            del air_cooler['PROCESS_power']
        except KeyError:
            return {}
        air_cooler['connectors'] = '4-pin pwm'
        try:
            air_cooler['height'] = math.ceil(float(air_cooler['PROCESS_height'].split()[0]))
            del air_cooler['PROCESS_height']
        except KeyError:
            return {}
        try:
            noise = air_cooler['PROCESS_noise_level'].replace(' дБ', '')
            if '-' in noise:
                noise = noise.split('-')[1]
            air_cooler['noise_level'] = float(noise)
            del air_cooler['PROCESS_noise_level']
        except KeyError:
            return {}
        air_cooler['coolant'] = 'air'
        return air_cooler

    def get_casecooler_info(self, url: str):
        valid_keys = {
            'Производитель' : 'manufacturer',
            'Код производителя' : 'model',
            'Размеры вентилятора (ДхШ)' : 'PROCESS_size',
            'Воздушный поток' : 'PROCESS_airflow',
            'Уровень шума' : 'PROCESS_noise_level',
            'Модульное соединение' : 'PROCESS_modular_joint',
            'Тип коннектора' : 'PROCESS_connector_pins'
        }
        string_fields = ['manufacturer', 'model']
        integer_fields = []
        boolean_fields = []
        air_cooler = self.get_component_info(url, valid_keys, string_fields, integer_fields, boolean_fields)
        if 'model' not in air_cooler.keys():
            return {}
        try:
            air_cooler['size'] = int(air_cooler['PROCESS_size'].split('x')[0])
            del air_cooler['PROCESS_size']
        except KeyError:
            return {}
        try:
            airflow = air_cooler['PROCESS_airflow'].replace(' CFM', '')
            if '-' in airflow:
                airflow = airflow.split('-')[1]
            air_cooler['airflow'] = float(airflow)
            del air_cooler['PROCESS_airflow']
        except KeyError:
            pass
        try:
            air_cooler['modular_joint'] = True if air_cooler['PROCESS_modular_joint'] == 'да' else False
            del air_cooler['PROCESS_modular_joint']
        except KeyError:
            air_cooler['modular_joint'] = False
        try:
            if '3-pin' in air_cooler['PROCESS_connector_pins']:
                air_cooler['connector_pins'] = '3-pin argb-5v'
            elif '4-pin' in air_cooler['PROCESS_connector_pins']:
                air_cooler['connector_pins'] = '4-pin pwm'
            else:
                air_cooler['connector_pins'] = air_cooler['PROCESS_connector_pins']
            del air_cooler['PROCESS_connector_pins']
        except KeyError:
            return {}
        try:
            noise = air_cooler['PROCESS_noise_level'].replace(' дБ', '')
            if '-' in noise:
                noise = noise.split('-')[1]
            air_cooler['noise_level'] = float(noise)
            del air_cooler['PROCESS_noise_level']
        except KeyError:
            return {}
        return air_cooler

    def get_ssd_info(self, url: str):
        valid_keys = {
            'Производитель' : 'manufacturer',
            'Код производителя' : 'model',
            'Тип' : 'PROCESS_type',
            'Форм-фактор' : 'PROCESS_interface',
            'Объём накопителя' : 'PROCESS_volume',
            'Скорость чтения' : 'PROCESS_rd_speed',
            'Скорость записи' : 'PROCESS_wr_speed'
        }
        string_fields = ['manufacturer', 'model']
        integer_fields = []
        boolean_fields = []
        disc = self.get_component_info(url, valid_keys, string_fields, integer_fields, boolean_fields)
        if 'model' not in disc.keys():
            return {}
        try:
            disc['type'] = disc['PROCESS_interface'].split()[0].split(',')[0] + ' ' + disc['PROCESS_type']
            del disc['PROCESS_type']
            del disc['PROCESS_interface']
        except KeyError:
            return {}
        try:
            disc['volume'] = int(disc['PROCESS_volume'].split()[0])
            del disc['PROCESS_volume']
        except KeyError:
            return {}
        try:
            disc['rd_speed'] = round(float(disc['PROCESS_rd_speed'].split()[0]))
            del disc['PROCESS_rd_speed']
        except KeyError:
            return {}
        try:
            disc['wr_speed'] = round(float(disc['PROCESS_wr_speed'].split()[0]))
            del disc['PROCESS_wr_speed']
        except KeyError:
            return {}
        return disc

    def get_hdd_info(self, url: str):
        valid_keys = {
            'Производитель' : 'manufacturer',
            'Код производителя' : 'model',
            'Тип' : 'PROCESS_type',
            'Форм-фактор' : 'PROCESS_interface',
            'Объём жёсткого диска' : 'PROCESS_volume'
        }
        string_fields = ['manufacturer', 'model']
        integer_fields = []
        boolean_fields = []
        disc = self.get_component_info(url, valid_keys, string_fields, integer_fields, boolean_fields)
        if 'model' not in disc.keys():
            return {}
        try:
            disc['type'] = disc['PROCESS_interface'].split()[0] + ' ' + disc['PROCESS_type']
            del disc['PROCESS_type']
            del disc['PROCESS_interface']
        except KeyError:
            return {}
        try:
            disc['volume'] = int(disc['PROCESS_volume'].split()[0])
            del disc['PROCESS_volume']
        except KeyError:
            return {}
        return disc

    # Функция, удаляющая из массива идентификаторов компонентов все, кроме идентификатора компонента с наименьшей ценой
    def remove_dublicates_from_group(self, components: list, group: list):
        prices = []
        for index in group:
            prices.append(components[index]['price'])
        new_group = [prices.index(min(prices))]
        return new_group

    # Функция, удаляющая дубликаты из массива компонентов
    def delete_dublicates(self, components: list, keys_to_remove: list):
        uids = []
        indexes = []
        comp_list = components
        for i in range(len(comp_list)):
            arr = list(comp_list[i].keys())
            for key in keys_to_remove:
                if key in arr:
                    arr.remove(key)
            arr.sort()
            uid = '|'.join(list(map(lambda x: str(comp_list[i].get(x)), arr)))
            if uid not in uids:
                uids.append(uid)
                indexes.append([i])
            else:
                idx = uids.index(uid)
                indexes[idx].append(i)
        indexes = list(map(lambda x: self.remove_dublicates_from_group(comp_list, x) if len(x) > 1 else x, indexes))
        new_components = merge_lists(indexes)
        new_components.sort()
        return list(map(lambda x: comp_list[x], new_components))

    def parse_components(self, component_type: str, component_path: str, qfilter: str, uid_ignored_fields: list):
        components = []
        counter = 0
        start = time.time()
        parsed = False
        links = self.collect_component_links(component_path, qfilter)
        control_count = len(links)
        print(Fore.MAGENTA + f'Links collected: {control_count}')
        for link in links:
            try_again = 2
            while parsed == False:
                try:
                    if component_type == 'processor':
                        components.append(self.get_processor_info(link))
                    elif component_type == 'motherboard':
                        components.append(self.get_motherboard_info(link))
                    elif component_type == 'videocard':
                        components.append(self.get_videocard_info(link))
                    elif component_type == 'memory':
                        components.append(self.get_memory_info(link))
                    elif component_type == 'cooler':
                        components.append(self.get_air_cooler_info(link))
                    elif component_type == 'case':
                        components.append(self.get_case_info(link))
                    elif component_type == 'ssd':
                        components.append(self.get_ssd_info(link))
                    elif component_type == 'hdd':
                        components.append(self.get_hdd_info(link))
                    elif component_type == 'casecooler':
                        components.append(self.get_casecooler_info(link))
                    elif component_type == 'powersupply':
                        components.append(self.get_powersupply_info(link))
                    else:
                        raise ValueError('Wrong component type!')
                    parsed = True
                except:
                    print(Fore.RED + f'Error occured while parsing link {link}')
                    if try_again > 0:
                        print(Fore.MAGENTA + 'Trying again...')
                        try_again -= 1
                        time.sleep(180)
                    else:
                        print(Fore.RED + 'Parsing link failed.')
                        raise RuntimeError
            print(Fore.MAGENTA + f'{links.index(link)+1}/{control_count} link parsed successfully.')
            parsed = False
        for component in components:
            if len(component.keys()) > 0:
                counter += 1
        if counter == control_count:
            print(Fore.MAGENTA + f'All {component_type} links processed successfully.')
        else:
            print(Fore.MAGENTA + f'{control_count-counter} {component_type} links lost.')
        components = list(map(lambda x: '__del__' if len(x.keys()) == 0 else x, components))
        while '__del__' in components:
            place = components.index('__del__')
            components.pop(place)
        components = self.delete_dublicates(components, uid_ignored_fields)
        print(Fore.MAGENTA + f'Removed {counter - len(components)} dublicates, totally parsed {len(components)} components.')
        print(Fore.MAGENTA + 'Saving components...')
        for component in components:
            if component_type == 'processor':
                save_processor(component)
            elif component_type == 'motherboard':
                save_motherboard(component)
            elif component_type == 'videocard':
                save_videocard(component)
            elif component_type == 'memory':
                save_memory(component)
            elif component_type == 'cooler':
                save_cooler(component)
            elif component_type == 'case':
                save_case(component)
            elif component_type == 'ssd':
                save_ssd(component)
            elif component_type == 'hdd':
                save_hdd(component)
            elif component_type == 'casecooler':
                save_casecooler(component)
            elif component_type == 'powersupply':
                save_powersupply(component)
            else:
                raise ValueError('Wrong component type!')
        print(Fore.MAGENTA + 'Components saved.')

def get_or_add_manufacturer(manufacturer: str):
        manufacturers = [name.upper() for name in Manufacturer.objects.values_list('name', flat=True)]
        uman = manufacturer.upper()
        if uman not in manufacturers:
            man = Manufacturer.objects.create(name=uman, description="")
        else:
            man = Manufacturer.objects.get(name = uman)
        return man

def save_processor(processor: dict):
    try:
        comp = Processor(
            manufacturer = get_or_add_manufacturer(processor['manufacturer']),
            series = processor['series'],
            model = processor['model'],
            socket = processor['socket'],
            cores = processor['cores'],
            p_cores = processor['p_cores'],
            e_cores = processor['e_cores'],
            threads = processor['threads'],
            frequency = processor['frequency'],
            turbo_freq = processor['turbo_freq'] if 'turbo_freq' in list(processor.keys()) else None,
            unlocked = processor['unlocked'],
            int_graphics = processor['int_graphics'],
            tdp = processor['tdp'],
            price = processor['price'],
            link = processor['link'],
            rating = processor['rate']
        )
        comp.save()
    except KeyError:
        print(Fore.RED + f'Error occured while saving processor: {processor}')
        raise KeyError

def save_motherboard(motherboard: dict):
    try:
        comp = Motherboard(
            manufacturer = get_or_add_manufacturer(motherboard['manufacturer']),
            model = motherboard['model'],
            socket = motherboard['socket'],
            chipset = motherboard['chipset'],
            formfactor = motherboard['formfactor'],
            mem_type = motherboard['mem_type'],
            mem_slots = motherboard['mem_slots'],
            wifi_ver = motherboard['wifi_ver'] if 'wifi_ver' in list(motherboard.keys()) else None,
            bluetooth_ver = motherboard['bluetooth_ver'] if 'bluetooth_ver' in list(motherboard.keys()) else None,
            sata_ports = motherboard['sata_ports'],
            connectors = motherboard['connectors'],
            internal_usb = motherboard['internal_usb'] if 'internal_usb' in list(motherboard.keys()) else None,
            pciex16_slots = motherboard['pciex16_slots'],
            pciex16_ver = motherboard['pciex16_ver'],
            pciex1_slots = motherboard['pciex1_slots'],
            m2_slots = motherboard['m2_slots'],
            backports = motherboard['backports'],
            price = motherboard['price'],
            link = motherboard['link']
        )
        comp.save()
    except KeyError:
        print(Fore.RED + f'Error occured while saving motherboard: {motherboard}')
        raise KeyError

def save_videocard(videocard: dict):
    try:
        comp = Videocard(
            manufacturer = get_or_add_manufacturer(videocard['manufacturer']),
            model = videocard['model'],
            chip = videocard['chip'],
            chip_manufacturer = get_or_add_manufacturer(videocard['chip_manufacturer']),
            pciex16_ver = videocard['pciex16_ver'],
            coolers = videocard['coolers'] if 'coolers' in list(videocard.keys()) else None,
            backports = videocard['backports'],
            frequency = videocard['frequency'],
            boost_freq = videocard['boost_freq'] if 'boost_freq' in list(videocard.keys()) else None,
            mem_volume = videocard['mem_volume'],
            mem_type = videocard['mem_type'],
            bus_width = videocard['bus_width'],
            bandwidth = videocard['bandwidth'] if 'bandwidth' in list(videocard.keys()) else None,
            max_monitors = videocard['max_monitors'],
            power_pins = videocard['power_pins'] if 'power_pins' in list(videocard.keys()) else None,
            psu_power = videocard['psu_power'],
            exp_slots = videocard['exp_slots'],
            length = videocard['length'],
            price = videocard['price'],
            link = videocard['link'],
            rating = videocard['rate']
        )
        comp.save()
    except KeyError:
        print(Fore.RED + f'Error occured while saving videocard: {videocard}')
        raise KeyError

def save_case(case: dict):
    try:
        comp = Case(
            manufacturer = get_or_add_manufacturer(case['manufacturer']),
            model = case['model'],
            typesize = case['typesize'] if 'typesize' in list(case.keys()) else None,
            mb_ffs = case['mb_ffs'],
            psu_typesize = case['psu_typesize'],
            big_sata_slots = case['big_sata_slots'],
            small_sata_slots = case['small_sata_slots'],
            max_gpu_length = case['max_gpu_length'],
            max_cooler_height = case['max_cooler_height'],
            max_psu_length = case['max_psu_length'] if 'max_psu_length' in list(case.keys()) else None,
            front_interfaces = case['front_interfaces'] if 'front_interfaces' in list(case.keys()) else None,
            cooler_slots = case['cooler_slots'] if 'cooler_slots' in list(case.keys()) else None,
            installed_coolers = case['installed_coolers'] if 'installed_coolers' in list(case.keys()) else None,
            exp_slots = case['exp_slots'],
            liquid_possible = case['liquid_possible'] if 'liquid_possible' in list(case.keys()) else False,
            width = case['width'] if 'width' in list(case.keys()) else None,
            height = case['height'] if 'height' in list(case.keys()) else None,
            length = case['length'] if 'length' in list(case.keys()) else None,
            mass = case['mass'] if 'mass' in list(case.keys()) else None,
            price = case['price'],
            link = case['link']
        )
        comp.save()
    except KeyError:
        print(Fore.RED + f'Error occured while saving case: {case}')
        raise KeyError

def save_memory(memory: dict):
    try:
        comp = Memory(
            manufacturer = get_or_add_manufacturer(memory['manufacturer']),
            model = memory['model'],
            mem_type = memory['mem_type'],
            volume = memory['volume'],
            frequency = memory['frequency'],
            bandwidth = memory['bandwidth'],
            latency = memory['latency'],
            price = memory['price'],
            link = memory['link']
        )
        comp.save()
    except KeyError:
        print(Fore.RED + f'Error occured while saving memory: {memory}')
        raise KeyError

def save_cooler(cooler: dict):
    try:
        comp = Cooler(
            manufacturer = get_or_add_manufacturer(cooler['manufacturer']),
            model = cooler['model'],
            coolant = cooler['coolant'],
            sockets = cooler['sockets'],
            power = cooler['power'],
            connectors = cooler['connectors'],
            modular_joint = None,
            height = cooler['height'],
            radiator_size = None,
            noise_level = cooler['noise_level'],
            price = cooler['price'],
            link = cooler['link']
        )
        comp.save()
    except KeyError:
        print(Fore.RED + f'Error occured while saving cooler: {cooler}')
        raise KeyError

def save_ssd(ssd: dict):
    try:
        comp = Disc(
            manufacturer = get_or_add_manufacturer(ssd['manufacturer']),
            model = ssd['model'],
            type = DiscType.objects.get(name = ssd['type']),
            volume = ssd['volume'],
            rd_speed = ssd['rd_speed'],
            wr_speed = ssd['wr_speed'],
            price = ssd['price'],
            link = ssd['link']
        )
        comp.save()
    except:
        print(Fore.RED + f'Error occured while saving ssd: {ssd}')
        raise KeyError

def save_hdd(hdd: dict):
    try:
        comp = Disc(
            manufacturer = get_or_add_manufacturer(hdd['manufacturer']),
            model = hdd['model'],
            type = DiscType.objects.get(name = hdd['type']),
            volume = hdd['volume'],
            rd_speed = None,
            wr_speed = None,
            price = hdd['price'],
            link = hdd['link']
        )
        comp.save()
    except KeyError:
        print(Fore.RED + f'Error occured while saving hdd: {hdd}')
        raise KeyError

def save_casecooler(casecooler: dict):
    try:
        comp = CaseCooler(
            manufacturer = get_or_add_manufacturer(casecooler['manufacturer']),
            model = casecooler['model'],
            size = casecooler['size'],
            airflow = casecooler['airflow'] if 'airflow' in list(casecooler.keys()) else None,
            noise_level = casecooler['noise_level'],
            modular_joint = casecooler['modular_joint'],
            connector_pins = casecooler['connector_pins'],
            price = casecooler['price'],
            link = casecooler['link']
        )
        comp.save()
    except KeyError:
        print(Fore.RED + f'Error occured while saving casecooler: {casecooler}')
        raise KeyError

def save_powersupply(powersupply: dict):
    try:
        comp = PowerSupply(
            manufacturer = get_or_add_manufacturer(powersupply['manufacturer']),
            model = powersupply['model'],
            power = powersupply['power'],
            typesize = powersupply['typesize'],
            pfc_act = powersupply['pfc_act'],
            connectors = powersupply['connectors'],
            certificate = Certificate.objects.get(name = '80 PLUS ' + powersupply['certificate']) if 'certificate' in list(powersupply.keys()) else None,
            modular_cables = powersupply['modular_cables'] if 'modular_cables' in list(powersupply.keys()) else False,
            length = powersupply['length'] if 'length' in list(powersupply.keys()) else None,
            price = powersupply['price'],
            link = powersupply['link']
        )
        comp.save()
    except KeyError:
        print(Fore.RED + f'Error occured while saving powersupply: {powersupply}')
        raise KeyError

def initial_data_insertion():
    disc_types = DiscType.objects.all().count()
    if disc_types > 0:
        print(Fore.YELLOW + 'Skipping disc types...')
    else:
        DiscType.objects.create(      
            name = '2.5" SSD',
            interface = 'SATA',
            slot = 'small'
        )
        DiscType.objects.create(      
            name = 'M.2 SSD',
            interface = 'PCI-E M.2',
            slot = 'M.2'
        )
        DiscType.objects.create(      
            name = '2.5" HDD',
            interface = 'SATA',
            slot = 'small'
        )
        DiscType.objects.create(      
            name = '3.5" HDD',
            interface = 'SATA',
            slot = 'big'
        )
    certificates = Certificate.objects.all().count()
    if certificates > 0:
        print(Fore.YELLOW + 'Skipping certificates...')
    else:
        Certificate.objects.create(
            name = '80 PLUS Standard',
            power_ratio = 80,
            icon = None
        )
        Certificate.objects.create(
            name = '80 PLUS Bronze',
            power_ratio = 85,
            icon = None
        )
        Certificate.objects.create(
            name = '80 PLUS Silver',
            power_ratio = 88,
            icon = None
        )
        Certificate.objects.create(
            name = '80 PLUS Gold',
            power_ratio = 91,
            icon = None
        )
        Certificate.objects.create(
            name = '80 PLUS Platinum',
            power_ratio = 93,
            icon = None
        )
        Certificate.objects.create(
            name = '80 PLUS Titanium',
            power_ratio = 95,
            icon = None
        )
    try:
        CaseCooler.objects.get(model='Предустановленный кулер')
    except ObjectDoesNotExist:
        basic_cooler = CaseCooler(
            manufacturer = None,
            model = 'Предустановленный кулер',
            size = None,
            airflow = None,
            noise_level = None,
            modular_joint = None,
            connector_pins = None,
            price = 0,
            link = None,
            manual = True
        )
        basic_cooler.save()

class Command(BaseCommand):
    def handle(self, **options):
        load_dotenv()
        to_run = os.getenv('INITIAL_DATA_INSERTION')
        if to_run == 'exec':
            print(Fore.CYAN + 'Starting initial data insertion...')
            initial_data_insertion()
            
            url = 'https://www.regard.ru'
            processor_path = '/catalog/1001/processory'
            motherboard_path = '/catalog/1000/materinskie-platy'
            videocard_path = '/catalog/1013/videokarty'
            case_path = '/catalog/1032/korpusa'
            powersupply_path = '/catalog/1225/bloki-pitaniya'
            memory_path = '/catalog/1010/operativnaya-pamyat'
            cooler_path = '/catalog/5162/kulery-dlya-processorov'
            casecooler_path = '/catalog/1004/ventilyatory-dlya-korpusa'
            ssd_path = '/catalog/1015/nakopiteli-ssd'
            hdd_path = '/catalog/1014/zhestkie-diski-hdd'

            interface = Api(url)

            component_types = []
            if Processor.objects.all().count() == 0:
                component_types.append('processor')
            else:
                print(Fore.YELLOW + 'Skipping processor...')
            if Motherboard.objects.all().count() == 0:
                component_types.append('motherboard')
            else:
                print(Fore.YELLOW + 'Skipping motherboard...')
            if Videocard.objects.all().count() == 0:
                component_types.append('videocard')
            else:
                print(Fore.YELLOW + 'Skipping videocard...')
            if Case.objects.all().count() == 0:
                component_types.append('case')
            else:
                print(Fore.YELLOW + 'Skipping case...')
            if PowerSupply.objects.all().count() == 0:
                component_types.append('powersupply')
            else:
                print(Fore.YELLOW + 'Skipping powersupply...')
            if Memory.objects.all().count() == 0:
                component_types.append('memory')
            else:
                print(Fore.YELLOW + 'Skipping memory...')
            if Cooler.objects.all().count() == 0:
                component_types.append('cooler')
            else:
                print(Fore.YELLOW + 'Skipping cooler ...')
            if CaseCooler.objects.all().count() <= 1:
                component_types.append('casecooler')
            else:
                print(Fore.YELLOW + 'Skipping casecooler...')
            if Disc.objects.all().count() == 0:
                component_types.append('hdd')
                component_types.append('ssd')
            else:
                print(Fore.YELLOW + 'Skipping disc...')
            for component_type in component_types:
                print(Fore.CYAN + f"Parsing {component_type}...")
                if component_type == 'processor':
                    interface.parse_components('processor', processor_path, '', ['link', 'price'])
                elif component_type == 'motherboard':
                    interface.parse_components('motherboard', motherboard_path, 'eyJieUNoYXIiOnsiMjQ5Ijp7InZhbHVlcyI6WzM2NTUxLDEyODc4LDEwNzZdLCJleGNlcHQiOnRydWV9fSwiYnlQcmljZSI6eyJtaW4iOjEwMDAwLCJtYXgiOjE2MDY4MH19', ['backports', 'internal_usb', 'connectors', 'link', 'price'])
                elif component_type == 'videocard':
                    interface.parse_components('videocard', videocard_path, '', ['backports', 'power_pins', 'link', 'price', 'exp_slots', 'bandwidth'])
                elif component_type == 'memory':
                    interface.parse_components('memory', memory_path, 'eyJieUNoYXIiOnsiNDgiOnsidmFsdWVzIjpbMTc4XSwiZXhjZXB0IjpmYWxzZX0sIjUxIjp7InZhbHVlcyI6WzE4MF0sImV4Y2VwdCI6ZmFsc2V9fSwiYnlQcmljZSI6eyJtaW4iOjIwMDAsIm1heCI6NzAyNDB9fQ', ['link', 'price'])
                elif component_type == 'cooler':
                    interface.parse_components('cooler', cooler_path, 'eyJieUNoYXIiOnsiNTQ5Ijp7InZhbHVlcyI6WzI4MTFdLCJleGNlcHQiOmZhbHNlfSwiMTAyODAiOnsidmFsdWVzIjpbNDIzNjJdLCJleGNlcHQiOmZhbHNlLCJjb3VudGVyIjp7IjQyMzYyIjoxfX19LCJieVByaWNlIjp7Im1pbiI6MTAwMCwibWF4IjoxNDM0MH19', ['link', 'price', 'sockets'])
                elif component_type == 'case':
                    interface.parse_components('case', case_path, 'eyJieUNoYXIiOnsiNjAiOnsiZXhjZXB0IjpmYWxzZX0sIjkzIjp7ImV4Y2VwdCI6ZmFsc2V9LCI5NSI6eyJ2YWx1ZXMiOlsxNTIwXSwiZXhjZXB0IjpmYWxzZX19LCJieVByaWNlIjp7Im1pbiI6NTAwMCwibWF4Ijo5Mjc1MH19', ['front_interfaces', 'cooler_slots', 'link', 'price', 'installed_coolers', 'mb_ffs', 'psu_typesize'])
                elif component_type == 'ssd':
                    interface.parse_components('ssd', ssd_path, 'eyJieUNoYXIiOnsiNTUyMiI6eyJ2YWx1ZXMiOlsyNjU0OV0sImV4Y2VwdCI6dHJ1ZX19LCJieVByaWNlIjp7Im1pbiI6NDAwMCwibWF4IjoxOTUyNzB9fQ', ['link', 'price'])
                elif component_type == 'hdd':
                    interface.parse_components('hdd', hdd_path, '', ['link', 'price'])
                elif component_type == 'casecooler':
                    interface.parse_components('casecooler', casecooler_path, 'eyJieUNoYXIiOnsiMjU3MyI6eyJ2YWx1ZXMiOls2ODE5XSwiZXhjZXB0IjpmYWxzZX0sIjI1NzQiOnsidmFsdWVzIjpbNjg1Miw2ODIxXSwiZXhjZXB0IjpmYWxzZX0sIjI1NzkiOnsidmFsdWVzIjpbMjQyOTcsODkwMCw2ODQ1XSwiZXhjZXB0Ijp0cnVlLCJjb3VudGVyIjp7IjY4NDUiOjEsIjg5MDAiOjEsIjI0Mjk3IjoxfX19LCJieVByaWNlIjp7Im1pbiI6NTAwLCJtYXgiOjE2MDcwfX0', ['link', 'price'])
                elif component_type == 'powersupply':
                    interface.parse_components('powersupply', powersupply_path, 'eyJieUNoYXIiOnsiMTY2Ijp7ImV4Y2VwdCI6ZmFsc2V9LCI0MzMiOnsidmFsdWVzIjpbMjc3NV0sImV4Y2VwdCI6dHJ1ZX0sIjQzNCI6eyJleGNlcHQiOmZhbHNlfSwiOTg2MiI6eyJleGNlcHQiOmZhbHNlfX0sImJ5UHJpY2UiOnsibWluIjo0MDAwLCJtYXgiOjU3MTAwfX0', ['link', 'price', 'connectors'])
            print(Fore.GREEN + 'Parsing completed!')
        elif to_run == 'skip':
            print(Fore.CYAN + "Skipping initial data insertion.")
            return
        else:
            print(Fore.RED + "Can't start initial data insertion. Check up environmental variables.")
            return
from django.db import models
from django.contrib.auth.models import User
from django.contrib.postgres.fields import ArrayField

# Таблица производителей компьютерных комплектующих
class Manufacturer(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=32)
    description = models.TextField(blank=True)
    official_site = models.CharField(max_length=64, null=True)

    def __str__(self):
        return f"{self.name}"

# Таблица типов накопителей данных
class DiscType(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=16)
    interface = models.CharField(max_length=10)
    slot = models.CharField(max_length=10)

    def __str__(self):
        return f"{self.name}"

# Таблица сертификатов БП 80 PLUS
class Certificate(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=16)
    power_ratio = models.PositiveSmallIntegerField(default=80)
    icon = models.ImageField(upload_to='certificates', null=True)

    def __str__(self):
        return f"{self.name}"

# Таблица процессоров
class Processor(models.Model):
    id = models.AutoField(primary_key=True, editable=True)
    manufacturer = models.ForeignKey(Manufacturer, on_delete=models.CASCADE) 
    series = models.CharField(max_length=24)
    model = models.CharField(max_length=16)
    socket = models.CharField(max_length=12)
    cores = models.PositiveSmallIntegerField()
    p_cores = models.PositiveSmallIntegerField()
    e_cores = models.PositiveSmallIntegerField()
    threads = models.PositiveSmallIntegerField()
    frequency = models.IntegerField()
    turbo_freq = models.IntegerField(null=True)
    unlocked = models.BooleanField()
    int_graphics = models.BooleanField()
    tdp = models.PositiveSmallIntegerField()
    price = models.IntegerField()
    link = models.TextField()
    rating= models.IntegerField(null=True)
    image = models.ImageField(upload_to='components/processor', null=True)
    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)
    manual = models.BooleanField(default=False)
    parser_delete = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.manufacturer.name} {self.series} {self.model}"

# Таблица материнских плат
class Motherboard(models.Model):
    id = models.AutoField(primary_key=True, editable=True)
    manufacturer = models.ForeignKey(Manufacturer, on_delete=models.CASCADE) 
    model = models.CharField(max_length=64)
    socket = models.CharField(max_length=12)
    chipset = models.CharField(max_length=8)
    formfactor = models.CharField(max_length=10)
    mem_type = models.CharField(max_length=8)
    mem_slots = models.PositiveSmallIntegerField()
    wifi_ver = models.CharField(max_length=5, null=True)
    bluetooth_ver = models.CharField(max_length=5, null=True)
    sata_ports = models.PositiveSmallIntegerField()
    connectors = models.JSONField()
    internal_usb = models.JSONField(null=True)
    pciex16_slots = models.PositiveSmallIntegerField()
    pciex16_ver = models.FloatField()
    pciex1_slots = models.PositiveSmallIntegerField()
    m2_slots = models.PositiveSmallIntegerField()
    backports = models.JSONField()
    price = models.IntegerField()
    link = models.TextField()
    image = models.ImageField(upload_to='components/motherboard', null=True)
    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)
    manual = models.BooleanField(default=False)
    parser_delete = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.manufacturer.name} {self.model}"

# Таблица видеокарт
class Videocard(models.Model):
    id = models.AutoField(primary_key=True, editable=True)
    manufacturer = models.ForeignKey(Manufacturer, on_delete=models.CASCADE, related_name='card_manufact') 
    model = models.CharField(max_length=64)
    chip = models.CharField(max_length=64)
    chip_manufacturer = models.ForeignKey(Manufacturer, on_delete=models.CASCADE, related_name='chip_manufact') 
    pciex16_ver = models.FloatField()
    coolers = models.PositiveSmallIntegerField(null=True)
    backports = models.JSONField()
    frequency = models.IntegerField()
    boost_freq = models.IntegerField(null=True)
    mem_volume = models.PositiveSmallIntegerField()
    mem_type = models.CharField(max_length=10)
    bus_width = models.IntegerField()
    bandwidth = models.IntegerField(null=True)
    max_monitors = models.PositiveSmallIntegerField()
    power_pins = models.JSONField(null=True)
    psu_power = models.PositiveSmallIntegerField()
    exp_slots = models.PositiveSmallIntegerField()
    length = models.PositiveSmallIntegerField()
    price = models.IntegerField()
    link = models.TextField()
    rating = models.IntegerField(null=True)
    image = models.ImageField(upload_to='components/videocard', null=True)
    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)
    manual = models.BooleanField(default=False)
    parser_delete = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.manufacturer.name} {self.model}"

# Таблица модулей оператитвной памяти
class Memory(models.Model):
    id = models.AutoField(primary_key=True, editable=True)
    manufacturer = models.ForeignKey(Manufacturer, on_delete=models.CASCADE) 
    model = models.CharField(max_length=64)
    mem_type = models.CharField(max_length=8)
    volume = models.PositiveSmallIntegerField()
    frequency = models.IntegerField()
    bandwidth = models.IntegerField()
    latency = models.PositiveSmallIntegerField()
    price = models.IntegerField()
    link = models.TextField()
    image = models.ImageField(upload_to='components/memory', null=True)
    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)
    manual = models.BooleanField(default=False)
    parser_delete = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.manufacturer.name} {self.model}"

# Таблица процессорных кулеров
class Cooler(models.Model):
    id = models.AutoField(primary_key=True, editable=True)
    manufacturer = models.ForeignKey(Manufacturer, on_delete=models.CASCADE) 
    model = models.CharField(max_length=64)
    coolant = models.CharField(max_length=10)
    sockets = ArrayField(models.CharField(max_length=12))
    power = models.PositiveSmallIntegerField()
    connectors = models.JSONField()
    modular_joint = models.BooleanField(null=True)
    height = models.PositiveSmallIntegerField()
    radiator_size = models.PositiveSmallIntegerField(null=True)
    noise_level = models.FloatField()
    price = models.IntegerField()
    link = models.TextField()
    image = models.ImageField(upload_to='components/cooler', null=True)
    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)
    manual = models.BooleanField(default=False)
    parser_delete = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.manufacturer.name} {self.model}"

# Таблица компьютерных корпусов
class Case(models.Model):
    id = models.AutoField(primary_key=True, editable=True)
    manufacturer = models.ForeignKey(Manufacturer, on_delete=models.CASCADE) 
    model = models.CharField(max_length=64)
    typesize = models.CharField(max_length=16, null=True)
    mb_ffs = ArrayField(models.CharField(max_length=10))
    psu_typesize = ArrayField(models.CharField(max_length=10))
    big_sata_slots = models.PositiveSmallIntegerField()
    small_sata_slots = models.PositiveSmallIntegerField()
    max_gpu_length = models.PositiveSmallIntegerField()
    max_cooler_height = models.PositiveSmallIntegerField()
    max_psu_length = models.PositiveSmallIntegerField(null=True)
    front_interfaces = models.JSONField(null=True)
    cooler_slots = models.JSONField(null=True)
    installed_coolers = models.JSONField(null=True)
    exp_slots = models.PositiveSmallIntegerField()
    liquid_possible = models.BooleanField(default=False)
    width = models.IntegerField(null=True)
    height = models.IntegerField(null=True)
    length = models.IntegerField(null=True)
    mass = models.CharField(max_length=5, null=True)
    price = models.IntegerField()
    link = models.TextField()
    image = models.ImageField(upload_to='components/case', null=True)
    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)
    manual = models.BooleanField(default=False)
    parser_delete = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.manufacturer.name} {self.model}"

# Таблица накопителей данных
class Disc(models.Model):
    id = models.AutoField(primary_key=True, editable=True)
    manufacturer = models.ForeignKey(Manufacturer, on_delete=models.CASCADE) 
    model = models.CharField(max_length=64)
    type = models.ForeignKey(DiscType, on_delete=models.CASCADE) 
    volume = models.IntegerField()
    rd_speed = models.IntegerField(null=True)
    wr_speed = models.IntegerField(null=True)
    price = models.IntegerField()
    link = models.TextField()
    image = models.ImageField(upload_to='components/disc', null=True)
    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)
    manual = models.BooleanField(default=False)
    parser_delete = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.manufacturer.name} {self.model}"

# Таблица корпусных кулеров
class CaseCooler(models.Model):
    id = models.AutoField(primary_key=True, editable=True)
    manufacturer = models.ForeignKey(Manufacturer, on_delete=models.CASCADE, null=True) 
    model = models.CharField(max_length=64)
    size = models.PositiveSmallIntegerField(null=True)
    airflow = models.FloatField(null=True)
    noise_level = models.FloatField(null=True)
    modular_joint = models.BooleanField(null=True)
    connector_pins = models.CharField(max_length=16, null=True)
    price = models.IntegerField()
    link = models.TextField(null=True)
    image = models.ImageField(upload_to='components/casecooler', null=True)
    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)
    manual = models.BooleanField(default=False)
    parser_delete = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.manufacturer.name} {self.model}"

# Таблица блоков питания
class PowerSupply(models.Model):
    id = models.AutoField(primary_key=True, editable=True)
    manufacturer = models.ForeignKey(Manufacturer, on_delete=models.CASCADE) 
    model = models.CharField(max_length=64)
    power = models.PositiveSmallIntegerField()
    typesize = models.CharField(max_length=10)
    pfc_act = models.BooleanField()
    connectors = models.JSONField()
    certificate = models.ForeignKey(Certificate, on_delete=models.SET_NULL, null=True, related_name="certificate", related_query_name="certificate") 
    modular_cables = models.BooleanField()
    length = models.PositiveSmallIntegerField(null=True)
    price = models.IntegerField()
    link = models.TextField()
    image = models.ImageField(upload_to='components/powersupply', null=True)
    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)
    manual = models.BooleanField(default=False)
    parser_delete = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.manufacturer.name} {self.model}"

# Таблица сборок
class Computer(models.Model):
    id = models.AutoField(primary_key=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=24)
    image = models.ImageField(null=True)
    processor = models.ForeignKey(Processor, on_delete=models.SET_NULL, null=True) 
    motherboard = models.ForeignKey(Motherboard, on_delete=models.SET_NULL, null=True) 
    videocard = models.ForeignKey(Videocard, on_delete=models.SET_NULL, null=True) 
    memory = models.ForeignKey(Memory, on_delete=models.SET_NULL, null=True) 
    memory_cnt = models.PositiveSmallIntegerField(null=True)
    powersupply = models.ForeignKey(PowerSupply, on_delete=models.SET_NULL, null=True) 
    case = models.ForeignKey(Case, on_delete=models.SET_NULL, null=True) 
    cooler = models.ForeignKey(Cooler, on_delete=models.SET_NULL, null=True) 
    casecoolers = models.JSONField(null=True)
    discs = ArrayField(models.IntegerField())
    price = models.IntegerField(null=True)
    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField()
    public = models.BooleanField(default=False)
    active = models.BooleanField(default=True)
    temporary = models.BooleanField(default=True)
    valid = models.BooleanField(default=False)

    def __str__(self):
        return f"({self.id}) {self.name} - {self.user.username}"

# Таблица приложений
class App(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=64)
    icon = models.ImageField(upload_to='apps', null=True)
    min_cpu_rating = models.IntegerField(null=True, blank=True)
    min_cpu_cores = models.PositiveSmallIntegerField(null=True, blank=True)
    min_cpu_freq = models.IntegerField(null=True, blank=True)
    min_gpu_rating = models.IntegerField(null=True, blank=True)
    min_gpu_volume = models.PositiveSmallIntegerField(null=True, blank=True)
    min_ram_volume = models.PositiveSmallIntegerField(null=True, blank=True)
    need_ssd = models.BooleanField(default=False)
    rec_cpu_rating = models.IntegerField(null=True, blank=True)
    rec_cpu_cores = models.PositiveSmallIntegerField(null=True, blank=True)
    rec_cpu_freq = models.IntegerField(null=True, blank=True)
    rec_gpu_rating = models.IntegerField(null=True, blank=True)
    rec_gpu_volume = models.PositiveSmallIntegerField(null=True, blank=True)
    rec_ram_volume = models.PositiveSmallIntegerField(null=True, blank=True)
    rec_ssd = models.BooleanField(default=False)
    disc_space = models.IntegerField(null=True)
    category = models.CharField(max_length=64, blank=True, default='')

    def __str__(self):
        return f"{self.name}"

# Таблица - архив недоступных комплектующих, подлежащих удалению
class ComponentArchive(models.Model):
    id = models.AutoField(primary_key=True)
    table = models.CharField(max_length=16)
    deleted_id = models.IntegerField()
    link = models.TextField()
    reason = models.CharField(max_length=32)
    deleted = models.DateTimeField(auto_now_add=True)

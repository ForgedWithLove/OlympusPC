from django.shortcuts import render, redirect
from pc_configurator.models import Manufacturer, Processor, Motherboard, Videocard, Memory, Cooler, Case, Disc, CaseCooler, PowerSupply, DiscType, Certificate, Computer, App
from django.core.paginator import Paginator
from django.db.models import Q
from django.http import QueryDict
from .forms import NewUserForm, GuestToUserForm
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.forms import AuthenticationForm
from django.contrib import messages
from guest_user.decorators import allow_guest_user
import json
from guest_user.functions import is_guest_user
from pc_configurator.functions import assembly_is_valid, get_error_desciption, get_warning_desciption, main_assembler, deactivate_active, if_none
import ast
from datetime import datetime
from pytz import timezone

def welcome(request):
    return render(
        request,
        'welcome.html')

@allow_guest_user
def assemble(request):
    if request.method == "POST":
        deactivate_active(request.user)
        blank_assembly = Computer.objects.filter(user=request.user, processor=None, motherboard=None, videocard=None, memory=None, powersupply=None, case=None, cooler=None, discs__len=0).first()
        if blank_assembly is not None:
            blank_assembly.active = True
            blank_assembly.save()
    try:
        current_computer = Computer.objects.get(user=request.user, active=True)
    except Computer.DoesNotExist:
        next_number = Computer.objects.filter(user=request.user, name__contains='Сборка №').order_by('-created').first()
        if next_number is not None:
            next_number = int(next_number.name.replace('Сборка №', '')) + 1
        else:
            next_number = 1
        current_computer = Computer(
            user = request.user,
            name = f'Сборка №{next_number}',
            discs = [],
            temporary = is_guest_user(request.user),
            modified = datetime.now(timezone('Europe/Moscow'))
        )
        current_computer.save()
    casecoolers = current_computer.casecoolers
    if casecoolers:
        casecoolers = json.loads(casecoolers)
        sides = casecoolers.keys()
        installed_casecoolers = {}
        for key in sides:
            try:
                installed_casecoolers[key] = (CaseCooler.objects.get(id=casecoolers[key]['id']))
            except KeyError:
                pass
    else:
        sides = []
        installed_casecoolers = {}
    discs = [Disc.objects.get(id=disc_id) for disc_id in current_computer.discs]
    is_valid = assembly_is_valid(current_computer)
    valid = is_valid[0]
    errors = list(map(lambda index: get_error_desciption(index), is_valid[1]))
    warnings = list(map(lambda index: get_warning_desciption(index), is_valid[2]))
    context = {
        "current_computer": current_computer,
        "sides": sides,
        "installed_casecoolers": installed_casecoolers,
        "discs": discs,
        "valid": valid,
        "errors": errors,
        "warnings": warnings,
    }
    return render(request, 'assemble.html', context)

def select_processor(request):
    if request.user.is_authenticated:
        #Копируем текущие параметры запроса
        params = request.GET.copy()
        #Удаляем параметры, которые не нужно запоминать
        if 'csrfmiddlewaretoken' in params:
            params.pop('csrfmiddlewaretoken')
        if 'prev_params' in params:
            params.pop('prev_params')
        if 'page' in params:
            params.pop('page')
        #Собираем со страницы предыдущие параметры запроса
        prev_params = QueryDict(request.GET.get('prev_params', ''))
        #Собираем фильтры по параметрам
        sorting = params.get('sort', '')
        socket_filter = params.getlist('socket', '')
        #Определяем порядок вывода компонентов
        if sorting == 'price_asc':
            order_by_field = 'price'
        elif sorting == 'price_desc':
            order_by_field = '-price'
        elif sorting == 'performance_asc':
            order_by_field = 'rating'
        elif sorting == 'performance_desc':
            order_by_field = '-rating'
        else:
            order_by_field = 'id'
        #Собираем компоненты для формирования данных в шаблон
        components = Processor.objects.filter(price__gt=0).select_related('manufacturer').order_by(order_by_field)
        #Формируем данные для вывода в шаблон
        sockets = components.order_by('socket').values_list('socket', flat=True).distinct()
        #Применяем фильтры к компонентам
        query = Q()
        for socket in socket_filter:
            query = query | Q(socket=socket)
        components = components.filter(query)
        #Разбиваем данные по страницам
        paginator = Paginator(components, 32)
        page_number = request.GET.get("page")
        page = paginator.get_page(page_number)
        context = {
            "page": page,
            "sockets": sockets,
            "params": params.urlencode()
        }
        return render(request, 'select_processor.html', context)
    else:
        return redirect('welcome')

def select_motherboard(request):
    if request.user.is_authenticated:
        #Копируем текущие параметры запроса
        params = request.GET.copy()
        #Удаляем параметры, которые не нужно запоминать
        if 'csrfmiddlewaretoken' in params:
            params.pop('csrfmiddlewaretoken')
        if 'prev_params' in params:
            params.pop('prev_params')
        if 'page' in params:
            params.pop('page')
        #Собираем со страницы предыдущие параметры запроса
        prev_params = QueryDict(request.GET.get('prev_params', ''))
        #Собираем фильтры по параметрам
        sorting = params.get('sort', '')
        socket_filter = params.getlist('socket', '')
        #Определяем порядок вывода компонентов
        if sorting == 'price_asc':
            order_by_field = 'price'
        elif sorting == 'price_desc':
            order_by_field = '-price'
        else:
            order_by_field = 'id'
        #Собираем компоненты для формирования данных в шаблон
        components = Motherboard.objects.filter(price__gt=0).select_related('manufacturer').order_by(order_by_field)
        #Формируем данные для вывода в шаблон
        sockets = components.order_by('socket').values_list('socket', flat=True).distinct()
        #Применяем фильтры к компонентам
        query = Q()
        for socket in socket_filter:
            query = query | Q(socket=socket)
        components = components.filter(query)
        #Разбиваем данные по страницам
        paginator = Paginator(components, 32)
        page_number = request.GET.get("page")
        page = paginator.get_page(page_number)
        context = {
            "page": page,
            "sockets": sockets,
            "params": params.urlencode()
        }
        return render(request, 'select_motherboard.html', context)
    else:
        return redirect('welcome')

def select_videocard(request):
    if request.user.is_authenticated:
        #Копируем текущие параметры запроса
        params = request.GET.copy()
        #Удаляем параметры, которые не нужно запоминать
        if 'csrfmiddlewaretoken' in params:
            params.pop('csrfmiddlewaretoken')
        if 'prev_params' in params:
            params.pop('prev_params')
        if 'page' in params:
            params.pop('page')
        #Собираем со страницы предыдущие параметры запроса
        prev_params = QueryDict(request.GET.get('prev_params', ''))
        #Собираем фильтры по параметрам
        sorting = params.get('sort', '')
        chip_filter = params.getlist('chip', '')
        #Определяем порядок вывода компонентов
        if sorting == 'price_asc':
            order_by_field = 'price'
        elif sorting == 'price_desc':
            order_by_field = '-price'
        elif sorting == 'performance_asc':
            order_by_field = 'rating'
        elif sorting == 'performance_desc':
            order_by_field = '-rating'
        else:
            order_by_field = 'id'
        #Собираем компоненты для формирования данных в шаблон
        components = Videocard.objects.filter(price__gt=0).select_related('manufacturer').order_by(order_by_field)
        #Формируем данные для вывода в шаблон
        chips = components.order_by('chip').values_list('chip', flat=True).distinct()
        #Применяем фильтры к компонентам
        query = Q()
        for chip in chip_filter:
            query = query | Q(chip=chip)
        components = components.filter(query)
        #Разбиваем данные по страницам
        paginator = Paginator(components, 32)
        page_number = request.GET.get("page")
        page = paginator.get_page(page_number)
        context = {
            "page": page,
            "chips": chips,
            "params": params.urlencode()
        }
        return render(request, 'select_videocard.html', context)
    else:
        return redirect('welcome')

def select_memory(request):
    if request.user.is_authenticated:
        #Копируем текущие параметры запроса
        params = request.GET.copy()
        #Удаляем параметры, которые не нужно запоминать
        if 'csrfmiddlewaretoken' in params:
            params.pop('csrfmiddlewaretoken')
        if 'prev_params' in params:
            params.pop('prev_params')
        if 'page' in params:
            params.pop('page')
        #Собираем со страницы предыдущие параметры запроса
        prev_params = QueryDict(request.GET.get('prev_params', ''))
        #Собираем фильтры по параметрам
        sorting = params.get('sort', '')
        type_filter = params.getlist('mem_type', '')
        #Определяем порядок вывода компонентов
        if sorting == 'price_asc':
            order_by_field = 'price'
        elif sorting == 'price_desc':
            order_by_field = '-price'
        else:
            order_by_field = 'id'
        #Собираем компоненты для формирования данных в шаблон
        components = Memory.objects.filter(price__gt=0).select_related('manufacturer').order_by(order_by_field)
        #Формируем данные для вывода в шаблон
        types = components.order_by('mem_type').values_list('mem_type', flat=True).distinct()
        #Применяем фильтры к компонентам
        query = Q()
        for mem_type in type_filter:
            query = query | Q(mem_type=mem_type)
        components = components.filter(query)
        #Разбиваем данные по страницам
        paginator = Paginator(components, 32)
        page_number = request.GET.get("page")
        page = paginator.get_page(page_number)
        context = {
            "page": page,
            "types": types,
            "params": params.urlencode()
        }
        return render(request, 'select_memory.html', context)
    else:
        return redirect('welcome')

def select_cooler(request):
    if request.user.is_authenticated:
        #Копируем текущие параметры запроса
        params = request.GET.copy()
        #Удаляем параметры, которые не нужно запоминать
        if 'csrfmiddlewaretoken' in params:
            params.pop('csrfmiddlewaretoken')
        if 'prev_params' in params:
            params.pop('prev_params')
        if 'page' in params:
            params.pop('page')
        #Собираем со страницы предыдущие параметры запроса
        prev_params = QueryDict(request.GET.get('prev_params', ''))
        #Собираем фильтры по параметрам
        sorting = params.get('sort', '')
        coolant_filter = params.getlist('coolant', '')
        #Определяем порядок вывода компонентов
        if sorting == 'price_asc':
            order_by_field = 'price'
        elif sorting == 'price_desc':
            order_by_field = '-price'
        else:
            order_by_field = 'id'
        #Собираем компоненты для формирования данных в шаблон
        components = Cooler.objects.filter(price__gt=0).select_related('manufacturer').order_by(order_by_field)
        #Формируем данные для вывода в шаблон
        coolants = components.order_by('coolant').values_list('coolant', flat=True).distinct()
        #Применяем фильтры к компонентам
        query = Q()
        for coolant in coolant_filter:
            query = query | Q(coolant=coolant)
        components = components.filter(query)
        #Разбиваем данные по страницам
        paginator = Paginator(components, 32)
        page_number = request.GET.get("page")
        page = paginator.get_page(page_number)
        context = {
            "page": page,
            "coolants": coolants,
            "params": params.urlencode()
        }
        return render(request, 'select_cooler.html', context)
    else:
        return redirect('welcome')

def select_case(request):
    if request.user.is_authenticated:
        #Копируем текущие параметры запроса
        params = request.GET.copy()
        #Удаляем параметры, которые не нужно запоминать
        if 'csrfmiddlewaretoken' in params:
            params.pop('csrfmiddlewaretoken')
        if 'prev_params' in params:
            params.pop('prev_params')
        if 'page' in params:
            params.pop('page')
        #Собираем со страницы предыдущие параметры запроса
        prev_params = QueryDict(request.GET.get('prev_params', ''))
        #Собираем фильтры по параметрам
        sorting = params.get('sort', '')
        typesize_filter = params.getlist('typesize', '')
        #Определяем порядок вывода компонентов
        if sorting == 'price_asc':
            order_by_field = 'price'
        elif sorting == 'price_desc':
            order_by_field = '-price'
        else:
            order_by_field = 'id'
        #Собираем компоненты для формирования данных в шаблон
        components = Case.objects.filter(price__gt=0).select_related('manufacturer').order_by(order_by_field)
        #Формируем данные для вывода в шаблон
        typesizes = components.order_by('typesize').values_list('typesize', flat=True).distinct()
        #Применяем фильтры к компонентам
        query = Q()
        for typesize in typesize_filter:
            query = query | Q(typesize=typesize)
        components = components.filter(query)
        #Разбиваем данные по страницам
        paginator = Paginator(components, 32)
        page_number = request.GET.get("page")
        page = paginator.get_page(page_number)
        context = {
            "page": page,
            "typesizes": typesizes,
            "params": params.urlencode()
        }
        return render(request, 'select_case.html', context)
    else:
        return redirect('welcome')

def select_disc(request):
    if request.user.is_authenticated:
        #Копируем текущие параметры запроса
        params = request.GET.copy()
        #Удаляем параметры, которые не нужно запоминать
        if 'csrfmiddlewaretoken' in params:
            params.pop('csrfmiddlewaretoken')
        if 'prev_params' in params:
            params.pop('prev_params')
        if 'page' in params:
            params.pop('page')
        #Собираем со страницы предыдущие параметры запроса
        prev_params = QueryDict(request.GET.get('prev_params', ''))
        #Собираем фильтры по параметрам
        sorting = params.get('sort', '')
        type_filter = params.getlist('type', '')
        #Определяем порядок вывода компонентов
        if sorting == 'price_asc':
            order_by_field = 'price'
        elif sorting == 'price_desc':
            order_by_field = '-price'
        else:
            order_by_field = 'id'
        #Собираем компоненты для формирования данных в шаблон
        components = Disc.objects.filter(price__gt=0).select_related('manufacturer').order_by(order_by_field)
        #Формируем данные для вывода в шаблон
        types = components.select_related('type').order_by('type_id').distinct('type_id')
        #Применяем фильтры к компонентам
        query = Q()
        for type_ in type_filter:
            query = query | Q(type=type_)
        components = components.filter(query)
        #Разбиваем данные по страницам
        paginator = Paginator(components, 32)
        page_number = request.GET.get("page")
        page = paginator.get_page(page_number)
        context = {
            "page": page,
            "types": types,
            "params": params.urlencode()
        }
        return render(request, 'select_disc.html', context)
    else:
        return redirect('welcome')

def select_casecooler(request):
    if request.user.is_authenticated:
        #Копируем текущие параметры запроса
        params = request.GET.copy()
        #Удаляем параметры, которые не нужно запоминать
        if 'csrfmiddlewaretoken' in params:
            params.pop('csrfmiddlewaretoken')
        if 'prev_params' in params:
            params.pop('prev_params')
        if 'page' in params:
            params.pop('page')
        #Собираем со страницы предыдущие параметры запроса
        prev_params = QueryDict(request.GET.get('prev_params', ''))
        #Собираем фильтры по параметрам
        sorting = params.get('sort', '')
        size_filter = params.getlist('size', '')
        #Определяем порядок вывода компонентов
        if sorting == 'price_asc':
            order_by_field = 'price'
        elif sorting == 'price_desc':
            order_by_field = '-price'
        else:
            order_by_field = 'id'
        #Собираем компоненты для формирования данных в шаблон
        components = CaseCooler.objects.filter(price__gt=0).select_related('manufacturer').order_by(order_by_field)
        #Формируем данные для вывода в шаблон
        sizes = components.order_by('size').values_list('size', flat=True).distinct()
        #Применяем фильтры к компонентам
        query = Q()
        for size in size_filter:
            query = query | Q(size=size)
        components = components.filter(query)
        #Разбиваем данные по страницам
        paginator = Paginator(components, 32)
        page_number = request.GET.get("page")
        page = paginator.get_page(page_number)
        context = {
            "page": page,
            "sizes": sizes,
            "params": params.urlencode()
        }
        return render(request, 'select_casecooler.html', context)
    else:
        return redirect('welcome')

def select_powersupply(request):
    if request.user.is_authenticated:
        #Копируем текущие параметры запроса
        params = request.GET.copy()
        #Удаляем параметры, которые не нужно запоминать
        if 'csrfmiddlewaretoken' in params:
            params.pop('csrfmiddlewaretoken')
        if 'prev_params' in params:
            params.pop('prev_params')
        if 'page' in params:
            params.pop('page')
        #Собираем со страницы предыдущие параметры запроса
        prev_params = QueryDict(request.GET.get('prev_params', ''))
        #Собираем фильтры по параметрам
        sorting = params.get('sort', '')
        typesize_filter = params.getlist('typesize', '')
        #Определяем порядок вывода компонентов
        if sorting == 'price_asc':
            order_by_field = 'price'
        elif sorting == 'price_desc':
            order_by_field = '-price'
        else:
            order_by_field = 'id'
        #Собираем компоненты для формирования данных в шаблон
        components = PowerSupply.objects.filter(price__gt=0).select_related('manufacturer').order_by(order_by_field)
        #Формируем данные для вывода в шаблон
        typesizes = components.order_by('typesize').values_list('typesize', flat=True).distinct()
        #Применяем фильтры к компонентам
        query = Q()
        for typesize in typesize_filter:
            query = query | Q(typesize=typesize)
        components = components.filter(query)
        #Разбиваем данные по страницам
        paginator = Paginator(components, 32)
        page_number = request.GET.get("page")
        page = paginator.get_page(page_number)
        context = {
            "page": page,
            "typesizes": typesizes,
            "params": params.urlencode()
        }
        return render(request, 'select_powersupply.html', context)
    else:
        return redirect('welcome')

def register_request(request):
    if request.method == "POST":
        form = NewUserForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user, backend='django.contrib.auth.backends.ModelBackend')
            messages.success(request, 'Регистрация успешна!')
            return redirect("get_info")
        messages.error(request, "Введена некорректная информация.")
    form = NewUserForm()
    return render (request=request, template_name="register.html", context={"register_form":form})

def login_request(request):
    if request.method == "POST":
        form = AuthenticationForm(data=request.POST)
        if form.is_valid():
            user = authenticate(username=request.POST['username'], password=request.POST['password'])
            if user:
                login(request, user, backend='django.contrib.auth.backends.ModelBackend')
                return redirect("get_info")
            else:
                messages.error(request, "Неверный логин или пароль.")
    form = AuthenticationForm()
    return render (request=request, template_name="login.html", context={"login_form":form})

def logout_request(request):
    logout(request)
    return redirect('welcome')

def convert_request(request):
    if request.method == "POST":
        form = GuestToUserForm(request.POST)
        if form.is_valid():
            current_user = request.user
            current_computer = Computer.objects.get(user=current_user, active=True)
            user = form.save()
            login(request, user, backend='django.contrib.auth.backends.ModelBackend')
            messages.success(request, 'Регистрация успешна!')
            current_computer.id = None
            current_computer.user = user
            current_computer.name = f'Сборка №1'
            current_computer.temporary = False
            current_computer.save()
            return redirect("get_info")
        messages.error(request, "Введена некорректная информация.")
    form = GuestToUserForm()
    return render (request=request, template_name="convert.html", context={"convert_form":form})

def add_processor(request):
    id = request.POST['id']
    current_computer = Computer.objects.get(user=request.user, active=True)
    component = Processor.objects.get(id=id)
    current_computer.processor = component
    current_computer.modified = datetime.now(timezone('Europe/Moscow'))
    current_computer.valid = False
    current_computer.price = None
    current_computer.save()
    return redirect('assemble')

def add_motherboard(request):
    id = request.POST['id']
    current_computer = Computer.objects.get(user=request.user, active=True)
    component = Motherboard.objects.get(id=id)
    current_computer.motherboard = component
    current_computer.modified = datetime.now(timezone('Europe/Moscow'))
    current_computer.valid = False
    current_computer.price = None
    current_computer.save()
    return redirect('assemble')

def add_videocard(request):
    id = request.POST['id']
    current_computer = Computer.objects.get(user=request.user, active=True)
    component = Videocard.objects.get(id=id)
    current_computer.videocard = component
    current_computer.modified = datetime.now(timezone('Europe/Moscow'))
    current_computer.valid = False
    current_computer.price = None
    current_computer.save()
    return redirect('assemble')

def add_memory(request):
    id = request.POST['id']
    current_computer = Computer.objects.get(user=request.user, active=True)
    component = Memory.objects.get(id=id)
    current_computer.memory = component
    current_computer.memory_cnt = 1
    current_computer.modified = datetime.now(timezone('Europe/Moscow'))
    current_computer.valid = False
    current_computer.price = None
    current_computer.save()
    return redirect('assemble')

def add_cooler(request):
    id = request.POST['id']
    current_computer = Computer.objects.get(user=request.user, active=True)
    component = Cooler.objects.get(id=id)
    current_computer.cooler = component
    current_computer.modified = datetime.now(timezone('Europe/Moscow'))
    current_computer.valid = False
    current_computer.price = None
    current_computer.save()
    return redirect('assemble')

def add_case(request):
    id = request.POST['id']
    current_computer = Computer.objects.get(user=request.user, active=True)
    component = Case.objects.get(id=id)
    current_computer.case = component
    big_res = {}
    res = {}
    sides = (json.loads(component.cooler_slots)).keys()
    installed = json.loads(component.installed_coolers)
    for side in sides:
        if side in installed:
            res['id'] = CaseCooler.objects.get(model='Предустановленный кулер').id
            res['count'] = installed[side]['Количество']
            res['size'] = installed[side]['Размер']
            big_res[side] = res
            res = {}
        else:
            big_res[side] = {}
    current_computer.casecoolers = json.dumps(big_res, sort_keys=True)
    current_computer.modified = datetime.now(timezone('Europe/Moscow'))
    current_computer.valid = False
    current_computer.price = None
    current_computer.save()
    return redirect('assemble')

def add_powersupply(request):
    id = request.POST['id']
    current_computer = Computer.objects.get(user=request.user, active=True)
    component = PowerSupply.objects.get(id=id)
    current_computer.powersupply = component
    current_computer.modified = datetime.now(timezone('Europe/Moscow'))
    current_computer.valid = False
    current_computer.price = None
    current_computer.save()
    return redirect('assemble')

def add_disc(request):
    id = int(request.POST['id'])
    current_computer = Computer.objects.get(user=request.user, active=True)
    current_computer.discs.append(id)
    current_computer.modified = datetime.now(timezone('Europe/Moscow'))
    current_computer.valid = False
    current_computer.price = None
    current_computer.save()
    return redirect('assemble')

def add_casecooler(request):
    id = int(request.POST['id'])
    side = request.POST['side']
    current_computer = Computer.objects.get(user=request.user, active=True)
    component = CaseCooler.objects.get(id=id)
    casecoolers = json.loads(current_computer.casecoolers)
    casecoolers[side]['id'] = id
    casecoolers[side]['count'] = 1
    casecoolers[side]['size'] = component.size
    current_computer.casecoolers = json.dumps(casecoolers)
    current_computer.modified = datetime.now(timezone('Europe/Moscow'))
    current_computer.valid = False
    current_computer.price = None
    current_computer.save()
    return redirect('assemble')

def delete_disc(request):
    id = int(request.POST['id'])
    current_computer = Computer.objects.get(user=request.user, active=True)
    current_computer.discs.remove(id)
    current_computer.modified = datetime.now(timezone('Europe/Moscow'))
    current_computer.valid = False
    current_computer.price = None
    current_computer.save()
    return redirect('assemble')

def inc_casecooler(request):
    side = request.POST['side']
    current_computer = Computer.objects.get(user=request.user, active=True)
    casecoolers = json.loads(current_computer.casecoolers)
    casecoolers[side]['count'] += 1
    current_computer.casecoolers = json.dumps(casecoolers)
    current_computer.modified = datetime.now(timezone('Europe/Moscow'))
    current_computer.valid = False
    current_computer.price = None
    current_computer.save()
    return redirect('assemble')

def dec_casecooler(request):
    side = request.POST['side']
    current_computer = Computer.objects.get(user=request.user, active=True)
    casecoolers = json.loads(current_computer.casecoolers)
    casecoolers[side]['count'] -= 1
    current_computer.casecoolers = json.dumps(casecoolers)
    current_computer.modified = datetime.now(timezone('Europe/Moscow'))
    current_computer.valid = False
    current_computer.price = None
    current_computer.save()
    return redirect('assemble')

def delete_casecooler(request):
    side = request.POST['side']
    current_computer = Computer.objects.get(user=request.user, active=True)
    casecoolers = json.loads(current_computer.casecoolers)
    casecoolers[side] = {}
    current_computer.casecoolers = json.dumps(casecoolers)
    current_computer.modified = datetime.now(timezone('Europe/Moscow'))
    current_computer.valid = False
    current_computer.price = None
    current_computer.save()
    return redirect('assemble')

def inc_memory(request):
    current_computer = Computer.objects.get(user=request.user, active=True)
    current_computer.memory_cnt *= 2
    current_computer.modified = datetime.now(timezone('Europe/Moscow'))
    current_computer.valid = False
    current_computer.price = None
    current_computer.save()
    return redirect('assemble')

def dec_memory(request):
    current_computer = Computer.objects.get(user=request.user, active=True)
    current_computer.memory_cnt /= 2
    current_computer.modified = datetime.now(timezone('Europe/Moscow'))
    current_computer.valid = False
    current_computer.price = None
    current_computer.save()
    return redirect('assemble')

def delete_memory(request):
    current_computer = Computer.objects.get(user=request.user, active=True)
    current_computer.memory = None
    current_computer.memory_cnt = None
    current_computer.modified = datetime.now(timezone('Europe/Moscow'))
    current_computer.valid = False
    current_computer.price = None
    current_computer.save()
    return redirect('assemble')

@allow_guest_user
def select_apps(request):
    apps = list(App.objects.all())
    app_lists = []
    while len(apps) > 0:
        app_lists.append(apps[:5])
        apps = apps[5:]
    context = {
        "apps": app_lists
    }
    return render(request, 'select_apps.html', context)

def select_chars(request):
    if request.user.is_authenticated:
        params = request.GET.dict()
        selected_apps = {}
        for key in params.keys():
            if "r-" in key:
                selected_apps[int(key.replace("r-", ""))] = params[key]
        manufacturers = Processor.objects.all().order_by('manufacturer').values_list('manufacturer', flat=True).distinct()
        manufacturers = list(map(lambda id: Manufacturer.objects.get(pk=id), manufacturers))
        sockets = Processor.objects.all().order_by('socket').values_list('socket', flat=True).distinct()
        chips = Videocard.objects.all().order_by('chip').values_list('chip', flat=True).distinct()
        typesizes = Case.objects.all().order_by('typesize').values_list('typesize', flat=True).distinct()
        max_monitors = Videocard.objects.order_by('-max_monitors').first().max_monitors
        min_memory = Memory.objects.order_by('volume').first().volume
        buf = Motherboard.objects.order_by('-mem_slots').first()
        max_memory = buf.mem_slots * Memory.objects.filter(mem_type=buf.mem_type).order_by('-volume').first().volume
        min_disc = Disc.objects.order_by('volume').first().volume
        context = {
            "manufacturers" : manufacturers,
            "sockets" : sockets,
            "chips" : chips,
            "typesizes" : typesizes,
            "max_monitors" : max_monitors,
            "max_memory" : max_memory,
            "min_memory" : min_memory,
            "min_disc" : min_disc,
            "selected_apps" : selected_apps,
        }
        return render(request, 'select_chars.html', context=context)
    else:
        return redirect('select_apps')

def auto_showcase(request):
    if request.user.is_authenticated:
        #Формируем полные списки комплектующих
        processor_qs = Processor.objects.all()
        motherboard_qs = Motherboard.objects.all()
        videocard_qs = Videocard.objects.all()
        memory_qs = Memory.objects.all()
        cooler_qs = Cooler.objects.all()
        case_qs = Case.objects.all()
        disc_qs = Disc.objects.all()
        casecooler_qs = CaseCooler.objects.all()
        powersupply_qs = PowerSupply.objects.all()
        #Применяем ограничения параметров к спискам
        params = request.GET.copy()
        any_volume = 0
        ssd_volume = 0
        min_ram_volume = 0
        psu_multiplier = 1
        cooler_multiplier = 1
        buf_cpu_rating = 0
        buf_cpu_cores = 0
        buf_cpu_freq = 0
        buf_gpu_rating = 0
        buf_gpu_volume = 0
        selected_apps = ast.literal_eval(params['selected_apps'])
        for id in selected_apps.keys():
            app = App.objects.get(pk=id)
            if selected_apps[id] == 'min':
                buf_cpu_rating = app.min_cpu_rating if app.min_cpu_rating is not None and buf_cpu_rating < app.min_cpu_rating else buf_cpu_rating
                buf_cpu_cores = app.min_cpu_cores if app.min_cpu_cores is not None and buf_cpu_cores < app.min_cpu_cores else buf_cpu_cores
                buf_cpu_freq = app.min_cpu_freq if app.min_cpu_freq is not None and buf_cpu_freq < app.min_cpu_freq else buf_cpu_freq
                buf_gpu_rating = app.min_gpu_rating if app.min_gpu_rating is not None and buf_gpu_rating < app.min_gpu_rating else buf_gpu_rating
                buf_gpu_volume = app.min_gpu_volume if app.min_gpu_volume is not None and buf_gpu_volume < app.min_gpu_volume else buf_gpu_volume
                min_ram_volume = app.min_ram_volume if app.min_ram_volume is not None and min_ram_volume < app.min_ram_volume else min_ram_volume
                if app.need_ssd:
                    ssd_volume += app.disc_space
                any_volume += app.disc_space
            elif selected_apps[id] == 'rec':
                buf_cpu_rating = app.rec_cpu_rating if app.rec_cpu_rating is not None and buf_cpu_rating < app.rec_cpu_rating else buf_cpu_rating
                buf_cpu_cores = app.rec_cpu_cores if app.rec_cpu_cores is not None and buf_cpu_cores < app.rec_cpu_cores else buf_cpu_cores
                buf_cpu_freq = app.rec_cpu_freq if app.rec_cpu_freq is not None and buf_cpu_freq < app.rec_cpu_freq else buf_cpu_freq
                buf_gpu_rating = app.rec_gpu_rating if app.rec_gpu_rating is not None and buf_gpu_rating < app.rec_gpu_rating else buf_gpu_rating
                buf_gpu_volume = app.rec_gpu_volume if app.rec_gpu_volume is not None and buf_gpu_volume < app.rec_gpu_volume else buf_gpu_volume
                min_ram_volume = app.rec_ram_volume if app.rec_ram_volume is not None and min_ram_volume < app.rec_ram_volume else min_ram_volume
                if app.rec_ssd:
                    ssd_volume += app.disc_space
                else:
                    any_volume += app.disc_space
            else:
                raise ValueError('Incorrect type of app requirements.')
        processor_qs = processor_qs.filter(rating__gte = buf_cpu_rating).filter(cores__gte = buf_cpu_cores).filter(frequency__gte = buf_cpu_freq)
        videocard_qs = videocard_qs.filter(rating__gte = buf_gpu_rating).filter(mem_volume__gte = buf_gpu_volume)
        if 'manufacturer' in params.keys():
            manufact = Manufacturer.objects.get(pk=int(params['manufacturer']))
            processor_qs = processor_qs.filter(manufacturer = manufact)
        if 'socket' in params.keys():
            processor_qs = processor_qs.filter(socket = params['socket'])
            motherboard_qs = motherboard_qs.filter(socket = params['socket'])
            cooler_qs = cooler_qs.filter(sockets__contains = [params['socket']])
        if 'videochip' in params.keys():
            videocard_qs = videocard_qs.filter(chip = params['videochip'])
        if 'maxmonitors' in params.keys():
            videocard_qs = videocard_qs.filter(max_monitors__gte = int(params['maxmonitors']))
        if 'discvol' in params.keys():
            any_volume = max(int(params['discvol']), any_volume)
        if 'ssdonly' in params.keys():
            ssd_types = DiscType.objects.filter(name__contains = 'SSD')
            query = Q()
            for type_ in ssd_types:
                query = query | Q(type = type_)
            disc_qs = disc_qs.filter(query)
            ssd_volume = any_volume
        if 'memvol' in params.keys():
            min_ram_volume = max(min_ram_volume, int(params['memvol']))
        if 'typesize' in params.keys():
            case_qs = case_qs.filter(typesize = params['typesize'])
        if 'overclock' in params.keys():
            processor_qs = processor_qs.filter(unlocked = True)
            motherboard_qs = motherboard_qs.filter(Q(chipset__contains = 'Z') | Q(chipset__contains = 'X') | (Q(chipset__contains = 'B') & Q(manufacturer = Manufacturer.objects.get(name = 'AMD'))))
            cooler_multiplier += 0.3
            psu_multiplier += 0.15
        if 'wifi' in params.keys():
            motherboard_qs = motherboard_qs.filter(wifi_ver__isnull = False).filter(bluetooth_ver__isnull = False)
        if 'maxprice' in params.keys():
            #!!!
            pass    
        if (len(processor_qs) == 0 or 
            len(motherboard_qs) == 0 or
            len(videocard_qs) == 0 or
            len(memory_qs) == 0 or
            len(cooler_qs) == 0 or
            len(case_qs) == 0 or
            len(disc_qs) == 0 or
            len(casecooler_qs) == 0 or
            len(powersupply_qs) == 0
        ):
            #!!!
            print('Невозможно автоматически создать сборку с указанными характеристиками.')
            return redirect('assemble')

        buf = processor_qs.order_by('socket').values_list('socket', flat=True).distinct()
        query = Q()
        for socket in buf:
            query = query | Q(socket = socket)
        motherboard_qs = motherboard_qs.filter(query)
        query = Q()
        for socket in buf:
            query = query | Q(sockets__contains = [socket])
        cooler_qs = cooler_qs.filter(query)

        buf = motherboard_qs.order_by('socket').values_list('socket', flat=True).distinct()
        query = Q()
        for socket in buf:
            query = query | Q(socket = socket)
        processor_qs = processor_qs.filter(query)
        query = Q()
        for socket in buf:
            query = query | Q(sockets__contains = [socket])
        cooler_qs = cooler_qs.filter(query)

        buf = cooler_qs.order_by('-power').first().power
        processor_qs = processor_qs.filter(tdp__lte = buf*10/11)

        buf = motherboard_qs.order_by('formfactor').values_list('formfactor', flat=True).distinct()
        query = Q()
        for ff in buf:
            query = query | Q(mb_ffs__contains = [ff])
        case_qs = case_qs.filter(query)

        buf = motherboard_qs.order_by('mem_type').values_list('mem_type', flat=True).distinct()
        query = Q()
        for memt in buf:
            query = query | Q(mem_type = memt)
        memory_qs = memory_qs.filter(query)

        buf = memory_qs.order_by('mem_type').values_list('mem_type', flat=True).distinct()
        query = Q()
        for memt in buf:
            query = query | Q(mem_type = memt)
        motherboard_qs = motherboard_qs.filter(query)

        buf = case_qs.order_by('-max_gpu_length').first().max_gpu_length
        videocard_qs = videocard_qs.filter(length__lte = buf)

        buf = case_qs.order_by('-max_cooler_height').first().max_cooler_height
        cooler_qs = cooler_qs.filter(height__lte = buf)

        buf = powersupply_qs.order_by('typesize').values_list('typesize', flat=True).distinct()
        query = Q()
        for tpsz in buf:
            query = query | Q(psu_typesize__contains = [tpsz])
        case_qs = case_qs.filter(query)

        if (len(processor_qs) == 0 or 
            len(motherboard_qs) == 0 or
            len(videocard_qs) == 0 or
            len(memory_qs) == 0 or
            len(cooler_qs) == 0 or
            len(case_qs) == 0 or
            len(disc_qs) == 0 or
            len(casecooler_qs) == 0 or
            len(powersupply_qs) == 0
        ):
            #!!!
            print('Невозможно автоматически создать сборку с указанными характеристиками.')
            return redirect('assemble')

        cheap, optimal, performant = main_assembler(
            {
                'processor' : processor_qs.filter(price__gt = 0),
                'motherboard' : motherboard_qs.filter(price__gt = 0),
                'videocard' : videocard_qs.filter(price__gt = 0),
                'memory' : memory_qs.filter(price__gt = 0),
                'cooler' : cooler_qs.filter(price__gt = 0),
                'case' : case_qs.filter(price__gt = 0),
                'disc' : disc_qs.filter(price__gt = 0),
                'casecooler' : casecooler_qs.filter(price__gt = 0),
                'powersupply' : powersupply_qs.filter(price__gt = 0)
            },
            {
                'any_volume' : any_volume,
                'ssd_volume' : ssd_volume,
                'min_ram_volume' : min_ram_volume,
                'psu_mult' : psu_multiplier,
                'cooler_mult' : cooler_multiplier
            }
        )
        
        context = {
            'cheap' : cheap,
            'optimal' : optimal,
            'performant' : performant
        }
        return render(request, 'showcase.html', context=context)
    else:
        return redirect('select_apps')

def auto_configuration(request):
    params = ast.literal_eval(request.GET['assembly'])
    deactivate_active(request.user)
    next_number = Computer.objects.filter(user=request.user, name__contains='Сборка №').order_by('-created').first()
    if next_number is not None:
        next_number = int(next_number.name.replace('Сборка №', '')) + 1
    else:
        next_number = 1
    generated_computer = Computer(
        user = request.user,
        name = f'Сборка №{next_number}',
        processor = Processor.objects.get(pk=params['processor']),
        motherboard = Motherboard.objects.get(pk=params['motherboard']),
        videocard = Videocard.objects.get(pk=params['videocard']),
        memory = Memory.objects.get(pk=params['memory']),
        memory_cnt = params['memory_cnt'],
        powersupply = PowerSupply.objects.get(pk=params['powersupply']),
        case = Case.objects.get(pk=params['case']),
        cooler = Cooler.objects.get(pk=params['cooler']),
        casecoolers = params['casecoolers'],
        discs = params['discs'],
        price = params['price'],
        temporary = is_guest_user(request.user),
        modified = datetime.now(timezone('Europe/Moscow'))
    )
    generated_computer.save()
    return redirect('assemble')

def save_assembly(request):
    params = request.POST.dict()
    current_computer = Computer.objects.get(user=request.user, active=True)
    old_price = current_computer.price
    old_public = current_computer.public
    old_name = current_computer.name
    discs_obj = list(map(lambda x: Disc.objects.get(pk=x), current_computer.discs))
    current_computer.price = sum([
        current_computer.processor.price,
        current_computer.motherboard.price,
        current_computer.videocard.price,
        current_computer.memory.price * current_computer.memory_cnt,
        current_computer.case.price,
        current_computer.cooler.price,
        sum([disc.price for disc in discs_obj]),
        sum([(CaseCooler.objects.get(pk=side['id']).price * side['count'] if 'id' in side.keys() else 0) for side in json.loads(current_computer.casecoolers).values()])
    ])
    if 'public' in params.keys():
        current_computer.public = True
    else:
        current_computer.public = False
    if params['name'] != '':
        current_computer.name = params['name']
    current_computer.valid = True
    if old_price != current_computer.price or old_public != current_computer.public or old_name != current_computer.name:
        current_computer.modified = datetime.now(timezone('Europe/Moscow'))
    current_computer.save()
    return redirect('get_info')

@allow_guest_user
def get_info(request):
    try:
        current_computer = Computer.objects.get(user=request.user, active=True)
    except Computer.DoesNotExist:
        next_number = Computer.objects.filter(user=request.user, name__contains='Сборка №').order_by('-created').first()
        if next_number is not None:
            next_number = int(next_number.name.replace('Сборка №', '')) + 1
        else:
            next_number = 1
        current_computer = Computer(
            user = request.user,
            name = f'Сборка №{next_number}',
            discs = [],
            temporary = is_guest_user(request.user),
            modified = datetime.now(timezone('Europe/Moscow'))
        )
        current_computer.save()
    all_computers = Computer.objects.filter(user=request.user).order_by('-modified')
    context = {
        'current_computer' : current_computer,
        'all_computers' : all_computers,
        'user' : request.user
    }
    return render(request, 'user_info.html', context = context)

def activate_assembly(request):
    id = request.POST['id']
    deactivate_active(request.user)
    requested_assembly = Computer.objects.get(pk=id)
    requested_assembly.active = True
    requested_assembly.save()
    return redirect('get_info')

def assembly_analysis(request):
    if request.user.is_authenticated:
        current_computer = Computer.objects.get(user=request.user, active=True)
        context = {
            'current_computer' : current_computer
        }
        categories = App.objects.order_by('category').values_list('category', flat=True).distinct()
        context['categories'] = categories
        context['stage'] = 1
        params = request.GET.dict()
        if 'category' in params.keys():
            apps = App.objects.filter(category=params['category']).order_by('name')
            context['category'] = params['category']
            context['apps'] = apps
            context['stage'] = 2
        if 'app' in params.keys():
            app = App.objects.get(pk=params['app'])
            context['app'] = app
            context['stage'] = 3
            minimal = {}
            recommended = {}
            minimal['processor'] = current_computer.processor.rating >= if_none(app.min_cpu_rating, 0) and current_computer.processor.cores >= if_none(app.min_cpu_cores, 0) and current_computer.processor.frequency >= if_none(app.min_cpu_freq, 0)
            minimal['videocard'] = current_computer.videocard.rating >= if_none(app.min_gpu_rating, 0) and current_computer.videocard.mem_volume >= if_none(app.min_gpu_volume, 0)
            minimal['memory'] = current_computer.memory.volume * current_computer.memory_cnt >= if_none(app.min_ram_volume, 0)
            sata_ssd = DiscType.objects.get(name='2.5" SSD')
            m2_ssd = DiscType.objects.get(name="M.2 SSD")
            flag = False
            for id in current_computer.discs:
                disc = Disc.objects.get(pk=id)
                if disc.volume >= app.disc_space and (not app.need_ssd or disc.type == sata_ssd or disc.type == m2_ssd):
                    flag = True
                    break
            minimal['disc'] = flag
            minimal['summary'] = minimal['processor'] and minimal['videocard'] and minimal['memory'] and minimal['disc']
            recommended['processor'] = current_computer.processor.rating >= if_none(app.rec_cpu_rating, 0) and current_computer.processor.cores >= if_none(app.rec_cpu_cores, 0) and current_computer.processor.frequency >= if_none(app.rec_cpu_freq, 0)
            recommended['videocard'] = current_computer.videocard.rating >= if_none(app.rec_gpu_rating, 0) and current_computer.videocard.mem_volume >= if_none(app.rec_gpu_volume, 0)
            recommended['memory'] = current_computer.memory.volume * current_computer.memory_cnt >= if_none(app.rec_ram_volume, 0)
            flag = False
            for id in current_computer.discs:
                disc = Disc.objects.get(pk=id)
                if disc.volume >= app.disc_space and (not app.rec_ssd or disc.type == sata_ssd or disc.type == m2_ssd):
                    flag = True
                    break
            recommended['disc'] = flag
            recommended['summary'] = recommended['processor'] and recommended['videocard'] and recommended['memory'] and recommended['disc']
            context['minimal'] = minimal
            context['recommended'] = recommended
            print(minimal, recommended)
        return render(request, 'assembly_analysis.html', context = context)
    else:
        return redirect('get_info')

def delete_assembly(request):
    id = request.POST['id']
    assembly = Computer.objects.get(pk=id)
    assembly.delete()
    return redirect('get_info')
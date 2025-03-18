from django.shortcuts import render, redirect
from pc_configurator.models import Manufacturer, Processor, Motherboard, Videocard, Memory, Cooler, Case, Disc, CaseCooler, PowerSupply, DiscType, Certificate, Computer
from django.core.paginator import Paginator
from django.db.models import Q
from django.http import QueryDict
from .forms import NewUserForm, GuestToUserForm
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.forms import AuthenticationForm
from django.contrib import messages
from guest_user.decorators import allow_guest_user
import json

def welcome(request):
    return render(
        request,
        'welcome.html')

@allow_guest_user
def assemble(request):
    try:
        current_computer = Computer.objects.get(user=request.user, active=True)
    except Computer.DoesNotExist:
        next_number = Computer.objects.filter(user=request.user).count() + 1
        current_computer = Computer(
            user = request.user,
            name = f'Сборка №{next_number}',
            discs = []
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
    context = {
        "current_computer": current_computer,
        "sides": sides,
        "installed_casecoolers": installed_casecoolers,
        "discs": discs,
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
            return redirect("assemble")
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
                return redirect("assemble")
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
            current_computer.save()
            return redirect("assemble")
        messages.error(request, "Введена некорректная информация.")
    form = GuestToUserForm()
    return render (request=request, template_name="convert.html", context={"convert_form":form})

def add_processor(request):
    id = request.POST['id']
    current_computer = Computer.objects.get(user=request.user, active=True)
    component = Processor.objects.get(id=id)
    current_computer.processor = component
    current_computer.save(update_fields=["processor"])
    return redirect('assemble')

def add_motherboard(request):
    id = request.POST['id']
    current_computer = Computer.objects.get(user=request.user, active=True)
    component = Motherboard.objects.get(id=id)
    current_computer.motherboard = component
    current_computer.save(update_fields=["motherboard"])
    return redirect('assemble')

def add_videocard(request):
    id = request.POST['id']
    current_computer = Computer.objects.get(user=request.user, active=True)
    component = Videocard.objects.get(id=id)
    current_computer.videocard = component
    current_computer.save(update_fields=["videocard"])
    return redirect('assemble')

def add_memory(request):
    id = request.POST['id']
    current_computer = Computer.objects.get(user=request.user, active=True)
    component = Memory.objects.get(id=id)
    current_computer.memory = component
    current_computer.save(update_fields=["memory"])
    return redirect('assemble')

def add_cooler(request):
    id = request.POST['id']
    current_computer = Computer.objects.get(user=request.user, active=True)
    component = Cooler.objects.get(id=id)
    current_computer.cooler = component
    current_computer.save(update_fields=["cooler"])
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
    current_computer.save(update_fields=["case", "casecoolers"])
    return redirect('assemble')

def add_powersupply(request):
    id = request.POST['id']
    current_computer = Computer.objects.get(user=request.user, active=True)
    component = PowerSupply.objects.get(id=id)
    current_computer.powersupply = component
    current_computer.save(update_fields=["powersupply"])
    return redirect('assemble')

def add_disc(request):
    id = int(request.POST['id'])
    current_computer = Computer.objects.get(user=request.user, active=True)
    current_computer.discs.append(id)
    current_computer.save(update_fields=["discs"])
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
    current_computer.save(update_fields=["casecoolers"])
    return redirect('assemble')

def delete_disc(request):
    id = int(request.POST['id'])
    current_computer = Computer.objects.get(user=request.user, active=True)
    current_computer.discs.remove(id)
    current_computer.save(update_fields=["discs"])
    return redirect('assemble')

def inc_casecooler(request):
    id = int(request.POST['id'])
    side = request.POST['side']
    current_computer = Computer.objects.get(user=request.user, active=True)
    casecoolers = json.loads(current_computer.casecoolers)
    casecoolers[side]['count'] += 1
    current_computer.casecoolers = json.dumps(casecoolers)
    current_computer.save(update_fields=["casecoolers"])
    return redirect('assemble')

def dec_casecooler(request):
    id = int(request.POST['id'])
    side = request.POST['side']
    current_computer = Computer.objects.get(user=request.user, active=True)
    casecoolers = json.loads(current_computer.casecoolers)
    casecoolers[side]['count'] -= 1
    current_computer.casecoolers = json.dumps(casecoolers)
    current_computer.save(update_fields=["casecoolers"])
    return redirect('assemble')

def delete_casecooler(request):
    side = request.POST['side']
    current_computer = Computer.objects.get(user=request.user, active=True)
    casecoolers = json.loads(current_computer.casecoolers)
    casecoolers[side] = {}
    current_computer.casecoolers = json.dumps(casecoolers)
    current_computer.save(update_fields=["casecoolers"])
    return redirect('assemble')
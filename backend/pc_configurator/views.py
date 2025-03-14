from django.shortcuts import render, redirect
from pc_configurator.models import Manufacturer, Processor, Motherboard, Videocard, Memory, Cooler, Case, Disc, CaseCooler, PowerSupply, DiscType, Certificate
from django.core.paginator import Paginator
from django.db.models import Q
from django.http import QueryDict
from .forms import NewUserForm, GuestToUserForm
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.forms import AuthenticationForm
from django.contrib import messages
from guest_user.decorators import allow_guest_user

def welcome(request):
    return render(
        request,
        'welcome.html')

@allow_guest_user
def assemble(request):
    return render(request, 'assemble.html')

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
            user = form.save()
            login(request, user, backend='django.contrib.auth.backends.ModelBackend')
            messages.success(request, 'Регистрация успешна!')
            return redirect("assemble")
        messages.error(request, "Введена некорректная информация.")
    form = GuestToUserForm()
    return render (request=request, template_name="convert.html", context={"convert_form":form})
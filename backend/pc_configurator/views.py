from django.shortcuts import render
from pc_configurator.models import Manufacturer, Processor, Motherboard, Videocard, Memory, Cooler, Case, Disc, CaseCooler, PowerSupply, DiscType, Certificate
from django.core.paginator import Paginator
from django.db.models import Q
from django.http import QueryDict

def welcome(request):
    return render(
        request,
        'welcome.html')

def configurator(request):
    return render(request, 'configurator.html')

def select_processor(request):
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

def select_motherboard(request):
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

def select_videocard(request):
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

def select_memory(request):
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

def select_cooler(request):
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

def select_case(request):
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

def select_disc(request):
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

def select_casecooler(request):
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

def select_powersupply(request):
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
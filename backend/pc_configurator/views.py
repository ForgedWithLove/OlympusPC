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
    components = Processor.objects.all().order_by(order_by_field)
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
    components = Motherboard.objects.all().order_by(order_by_field)
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
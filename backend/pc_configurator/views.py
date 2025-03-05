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
    params = request.GET.copy()
    if 'csrfmiddlewaretoken' in params:
        params.pop('csrfmiddlewaretoken')
    if 'prev_params' in params:
        params.pop('prev_params')
    if 'page' in params:
        params.pop('page')
    prev_params = QueryDict(request.GET.get('prev_params', ''))
    print(params)
    print(prev_params)
    if 'socket' in prev_params and 'socket' not in params:
        params.setlist('socket', prev_params.getlist('socket'))
    print(params)

    socket_filter = params.getlist('socket', '')

    components = Processor.objects.all().order_by('id')
    sockets = components.order_by('socket').values_list('socket', flat=True).distinct()
    
    query = Q()
    for socket in socket_filter:
        query = query | Q(socket=socket)

    components = components.filter(query)

    paginator = Paginator(components, 32)
    page_number = request.GET.get("page")
    page = paginator.get_page(page_number)
    mnfs = Manufacturer.objects.all()
    manufacturers = {}
    for manufacturer in mnfs:
        manufacturers[manufacturer.id] = manufacturer.name
    context = {
        "page": page,
        "manufacturers": manufacturers,
        "sockets": sockets,
        "params": params.urlencode()
    }
    return render(request, 'select_processor.html', context) 
from django.shortcuts import render
from pc_configurator.models import Manufacturer, Processor, Motherboard, Videocard, Memory, Cooler, Case, Disc, CaseCooler, PowerSupply, DiscType, Certificate
from django.core.paginator import Paginator

def welcome(request):
    return render(
        request,
        'welcome.html')

def configurator(request):
    return render(request, 'configurator.html')

def select_processor(request):
    components = Processor.objects.all()
    paginator = Paginator(components, 32)
    page_number = request.GET.get("page")
    page = paginator.get_page(page_number)
    mnfs = Manufacturer.objects.all()
    manufacturers = {}
    for manufacturer in mnfs:
        manufacturers[manufacturer.id] = manufacturer.name
    context = {
        "page": page,
        "manufacturers": manufacturers
    }
    return render(request, 'select_processor.html', context) 
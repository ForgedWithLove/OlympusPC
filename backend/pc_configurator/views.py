from django.shortcuts import render
from pc_configurator.models import Manufacturer, Processor, Motherboard, Videocard, Memory, Cooler, Case, Disc, CaseCooler, PowerSupply, DiscType, Certificate

def welcome(request):
    return render(
        request,
        'welcome.html')

def configurator(request):
    return render(request, 'configurator.html')

def select_processor(request):
    cpus = Processor.objects.all()
    mnfs = Manufacturer.objects.all()
    manufacturers = {}
    for manufacturer in mnfs:
        manufacturers[manufacturer.id] = manufacturer.name
    context = {
        "cpus": cpus,
        "manufacturers": manufacturers
    }
    return render(request, 'select_processor.html', context) 
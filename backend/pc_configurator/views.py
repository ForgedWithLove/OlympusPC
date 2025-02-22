from django.shortcuts import render

def welcome(request):
    return render(
        request,
        'welcome.html')

def configurator(request):
    return render(request, 'configurator.html')
from django.shortcuts import render

def index(request):
    return render(request, 'index.html')  # Загружаем шаблон index.html


def catalog(request):
    products = Product.objects.all()
    return render(request, 'catalog.html', {'products': products})

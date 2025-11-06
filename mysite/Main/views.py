from django.http import HttpResponse
from django.shortcuts import render

# Create your views here
def main(request):
    return render(request, 'main.html')

def contacts(request):
    return render(request, 'contacts.html')

def catalog(request):
    return render(request, 'catalog.html')

def payment(request):
    return render(request, 'payment.html')


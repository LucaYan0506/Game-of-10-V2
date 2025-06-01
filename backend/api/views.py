from django.shortcuts import render
from django.http import HttpResponse

# Create your views here.
def index_view(request):
    return render(request,"404page.html")
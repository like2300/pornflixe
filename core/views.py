from django.shortcuts import render
from django.views.generic import TemplateView
from .models import *
 

class HomeView(TemplateView):
    template_name = 'pages/staticpages/home.html'
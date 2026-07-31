from django.shortcuts import render
from django.views import generic


class HomePageView(generic.ListView):
    template_name = "core/home.html"

class AboutPageView(generic.TemplateView):
    template_name = "core/about.html"
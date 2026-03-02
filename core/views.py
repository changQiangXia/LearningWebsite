from django.http import HttpResponse
from django.shortcuts import render


def home(request):
    """Project landing page used during early development."""
    return render(request, "core/home.html")


def health(request):
    """Lightweight health endpoint for quick sanity checks."""
    return HttpResponse("ok")

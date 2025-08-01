from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.http import JsonResponse
from django.db import connection

def index(request):
    if request.user.is_authenticated:
        return redirect('statement:dashboard') # Redirect to dashboard if logged in
    
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)
            return redirect('statement:dashboard')
        else:
            messages.error(request, 'Invalid credentials')
            return redirect('pages:index')
            
    return render(request, 'pages/index.html')

def logout_view(request):
    logout(request)
    messages.success(request, 'You have been logged out.')
    return redirect('pages:index')

def health_check(request):
    """Health check endpoint for load balancer and monitoring"""
    try:
        # Check database connection
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        
        return JsonResponse({
            'status': 'healthy',
            'database': 'connected',
            'timestamp': request.META.get('HTTP_DATE', 'unknown')
        })
    except Exception as e:
        return JsonResponse({
            'status': 'unhealthy',
            'error': str(e),
            'timestamp': request.META.get('HTTP_DATE', 'unknown')
        }, status=503)

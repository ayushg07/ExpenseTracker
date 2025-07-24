from django.shortcuts import render

# Create your views here.

from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib import messages


def home(request):
    return render(request, 'expenses/home.html')

def register_user(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        if User.objects.filter(username=username).exists():
            messages.error(request, 'Username already exists')
            return redirect('register')
        user = User.objects.create_user(username=username, password=password)
        user.save()
        messages.success(request, 'Registered successfully! Please log in.')
        return redirect('login')
    return render(request, 'expenses/register.html')

def login_user(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user:
            login(request, user)
            return redirect('home')
        else:
            messages.error(request, 'Invalid credentials')
            return redirect('login')
    return render(request, 'expenses/login.html')

def logout_user(request):
    logout(request)
    return redirect('login')


from django.contrib.auth.decorators import login_required
from .models import Expense

@login_required
def dashboard(request):
    expenses = Expense.objects.filter(user=request.user).order_by('-date')
    return render(request, 'expenses/dashboard.html', {'expenses': expenses})


from .forms import ExpenseForm
from django.shortcuts import redirect

@login_required
def add_expense(request):
    if request.method == 'POST':
        form = ExpenseForm(request.POST)
        if form.is_valid():
            expense = form.save(commit=False)
            expense.user = request.user  # Link expense to logged-in user
            expense.save()
            return redirect('dashboard')
    else:
        form = ExpenseForm()
    return render(request, 'expenses/add_expense.html', {'form': form})

from django.shortcuts import get_object_or_404
@login_required
def edit_expense(request, expense_id):
    expense = get_object_or_404(Expense, id=expense_id, user=request.user)

    if request.method == 'POST':
        form = ExpenseForm(request.POST, instance=expense)
        if form.is_valid():
            form.save()
            return redirect('dashboard')
    else:
        form = ExpenseForm(instance=expense)
    
    return render(request, 'expenses/edit_expense.html', {'form': form})

@login_required
def delete_expense(request, expense_id):
    expense = get_object_or_404(Expense, id=expense_id, user=request.user)
    if request.method == 'POST':
        expense.delete()
        return redirect('dashboard')
    return render(request, 'expenses/delete_expense.html', {'expense': expense})


#Add Filtering

from django.db.models import Sum
from datetime import datetime

@login_required
def dashboard(request):
    expenses = Expense.objects.filter(user=request.user).order_by('-date')

    # Get filter values from GET params
    category = request.GET.get('category')
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')

    if category and category != 'All':
        expenses = expenses.filter(category=category)

    if start_date:
        expenses = expenses.filter(date__gte=start_date)

    if end_date:
        expenses = expenses.filter(date__lte=end_date)

    # Calculate total spent for charts
    total_by_category = expenses.values('category').annotate(total=Sum('amount'))

    context = {
        'expenses': expenses,
        'total_by_category': total_by_category,
    }
    return render(request, 'expenses/dashboard.html', context)

from django.core.serializers.json import DjangoJSONEncoder
import json

@login_required
def dashboard(request):
    expenses = Expense.objects.filter(user=request.user)
    total_by_category = expenses.values('category').annotate(total=Sum('amount'))
    context = {
        'expenses': expenses,
        'total_by_category': total_by_category,
        'total_by_category_json': json.dumps(list(total_by_category), cls=DjangoJSONEncoder),
    }
    return render(request, 'expenses/dashboard.html', context)
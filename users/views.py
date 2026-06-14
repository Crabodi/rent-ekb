from django.shortcuts import render, redirect
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views import View
from django.views.generic import CreateView, TemplateView
from django.urls import reverse_lazy
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth import get_user_model
from users.forms import UserRegisterForm

User = get_user_model()

class HomeView(TemplateView):
    template_name = 'properties/home.html'


class LoginView(View):
    """Страница входа"""
    template_name = 'users/login.html'
    
    def get(self, request):
        if request.user.is_authenticated:
            return redirect('home')
        return render(request, self.template_name)
    
    def post(self, request):
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        
        if user:
            login(request, user)
            next_url = request.GET.get('next', 'home')
            return redirect(next_url)
        else:
            messages.error(request, 'Неверное имя пользователя или пароль')
            return render(request, self.template_name)


class LogoutView(View):
    """Выход из системы"""
    def get(self, request):
        logout(request)
        return redirect('home')


class RegisterView(CreateView):
    """Регистрация пользователя"""
    template_name = 'users/register.html'
    form_class = UserRegisterForm
    success_url = reverse_lazy('login')
    
    def form_valid(self, form):
        messages.success(self.request, 'Регистрация успешна! Теперь вы можете войти.')
        return super().form_valid(form)
    
    def form_invalid(self, form):
        for field, errors in form.errors.items():
            for error in errors:
                messages.error(self.request, f'{field}: {error}')
        return super().form_invalid(form)


class ProfileView(LoginRequiredMixin, TemplateView):
    template_name = 'users/profile.html'
    login_url = 'login'


class MyPropertiesView(LoginRequiredMixin, TemplateView):
    template_name = 'properties/my_properties.html'
    login_url = 'login'


class MyBookingsView(LoginRequiredMixin, TemplateView):
    template_name = 'bookings/my_bookings.html'
    login_url = 'login'


class PropertyDetailView(TemplateView):
    template_name = 'properties/detail.html'


class CreatePropertyView(LoginRequiredMixin, TemplateView):
    template_name = 'properties/create.html'
    login_url = 'login'
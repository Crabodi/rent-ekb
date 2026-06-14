from django.shortcuts import render, redirect
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views import View
from django.views.generic import TemplateView
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.tokens import RefreshToken
from users.forms import UserRegisterForm

User = get_user_model()

class BaseContextMixin(TemplateView):
    """Базовый миксин для добавления токена в контекст"""
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.user.is_authenticated:
            # Получаем токен из сессии или создаем новый
            access_token = self.request.session.get('access_token')
            if not access_token:
                # Создаем новый токен если нет
                refresh = RefreshToken.for_user(self.request.user) # type: ignore
                access_token = str(refresh.access_token)
                self.request.session['access_token'] = access_token
                self.request.session['refresh_token'] = str(refresh)
            context['access_token'] = access_token
        return context

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

            # Создаем JWT токены и сохраняем в сессию
            refresh = RefreshToken.for_user(user)
            request.session['access_token'] = str(refresh.access_token)
            request.session['refresh_token'] = str(refresh)
            request.session['token_created_at'] = str(refresh.current_time)

            next_url = request.GET.get('next', 'home')
            return redirect(next_url)
        else:
            messages.error(request, 'Неверное имя пользователя или пароль')
            return render(request, self.template_name)


class LogoutView(View):
    """Выход из системы"""
    def get(self, request):
        # Очищаем сессию
        request.session.flush()
        logout(request)
        return redirect('home')


class RegisterView(View):
    """Регистрация пользователя"""
    template_name = 'users/register.html'
    
    def get(self, request):
        if request.user.is_authenticated:
            return redirect('home')
        form = UserRegisterForm()
        return render(request, self.template_name, {'form': form})
    
    def post(self, request):
        form = UserRegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            messages.success(request, 'Регистрация успешна! Теперь вы можете войти.')
            return redirect('login')
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f'{error}')
        return render(request, self.template_name, {'form': form})


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
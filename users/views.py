from django.contrib import messages
from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from .forms import CustomUserLoginForm, CustomUserUpdateForm, CustomUserCreationForm, PasswordResetRequestForm, PasswordResetConfirmForm
from .models import CustomUser

# New
from .tasks import send_welcome_email, send_password_reset_email, send_account_activation_email
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_decode
from django.utils.encoding import force_str
import logging

from .tokens import account_activation_token


def register(request):
    if request.method == 'POST': # Перевіряємо на пост запит. Спрацьовуватиме тоді коли буде пост запит
        form = CustomUserCreationForm(request.POST) # Ініціалізуємо запит. реквест пост дані які він нам дав
        if form.is_valid(): #Даними ми форму заповнили. Якщо форма валідна. Валідації які ми прописували
            user = form.save() # Зберігаємо користувача
            user.email_confirmed = False # Вказуємо що пошта не активована
            user.save()
            login(request, user, backend='django.contrib.auth.backends.ModelBackend')
            # логінимо збереженого користувача і передаємо бекенд для того щоб запобігти конфліктів з дефолтним бекендом

            send_welcome_email.delay(user.email, user.first_name) # Відправляємо повідомлення. В таску передали пошту і ім'я

            return redirect('users:profile')  # Редіректимо на профіль
    else:
        form = CustomUserCreationForm() # Якщо форма не валідна. Виводимо пусту форму і помилки
    return render(request, 'users/register.html', {'form': form})

def login_view(request):
    if request.method == 'POST':
        form = CustomUserLoginForm(request=request, data=request.POST) # Дата це дані які заповнюють
        if form.is_valid():
            user = form.get_user() # В юзер переміщуємо користувача. Стандартна перевірка джанго яка дістає користувача який є в системі

            login(request, user, backend='django.contrib.auth.backends.ModelBackend')
            return redirect('users:profile')
    else:
        form = CustomUserLoginForm()
    return render(request, 'users/login.html', {'form': form})

@login_required
def profile_views(request): # Для перегляду профіля

    return render(request, 'users/profile.html', {'user': request.user}) # Передаємо в контекст даного юзера

# Представлення для htmx. Яке динамічно міняє контент сторінки без перезагрузки роблячи запити до серверу
@login_required
def account_details(request):
    user = CustomUser.objects.get(id=request.user.id) # Беремо дані поточного користувача
    return render(request, 'users/partials/account_details.html', {'user': user})

@login_required
def edit_account_details(request):
    form = CustomUserUpdateForm(instance=request.user)
    return render(request, 'users/partials/edit_account_details.html',
                  {'user': request.user, 'form': form})


@login_required
def update_account_details(request):
    if request.method == 'POST':
        form = CustomUserUpdateForm(request.POST, instance=request.user)
        if form.is_valid():
            user = form.save(commit=False)
            user.clean()
            user.save()
            return render(request, 'users/partials/account_details.html', {'user': user})
        else:
            return render(request, 'users/partials/edit_account_details.html', {'user': request.user, 'form': form})
    return render(request, 'users/partials/account_details.html', {'user': request.user})

def logout_view(request):
    logout(request)
    return redirect('users:login')



def password_reset_request(request): # Надіслати запит на зміну пароля
    if request.method == 'POST': # Якщо надсилаємо форму
        form = PasswordResetRequestForm(request.POST) # Ініціалізуємо форму з даними
        if form.is_valid(): # Якщо дані валідні
            email = form.cleaned_data['email'] # Беремо пошту з очищених даних з ініціалізованої форми
            user = CustomUser.objects.filter(email=email).first() # Беремо користувача який це надіслав за допомогою пошти яку ми взяли вище
            if user: # Якщо такий користувач існує
                logging.info(f'Attempting to send password reset email to {email}, for user id {user.pk}') # Логуємо початок

                send_password_reset_email.delay(email, user.pk) # Запускаємо таску на пошту, передаючи емейл і ід користувача

                messages.success(request, 'Скидання пароля в черзі. Будь ласка, перевірте свою поштову скриньку для того щоб скинути пароль.')
                # Повідомлення відправлено очікуйте для користувача
                return render(request, 'users/password_reset_done.html', {'email': email})  # Рендеримо сторінку на якій буде повідомлення представленне вище
            else:
                messages.warning(request, 'Не знайдено акаунта для цієї пошти.') # Нема акаунта повідомлення
        else:
            messages.warning(request, 'Введіть правильну електронну адресу.') # Неправильно заповнена форма
    else:
        form = PasswordResetRequestForm() # Ініціалізація для сторінки, та сама сторінка х переданим контекстом форми
    return render(request, 'users/password_reset_request.html', {'form': form})


def password_reset_confirm(request, uidb64, token): # Коли користувач перейшов за посиланням видачі нового пароля
    # Приймаємо запит, юідб64 і токен який є в тасці. Перейшов по посиланню, ми по цьому посиланню приймаємо ці 2 елемента
    # Які згенеровані для користувача і відправлені в вигляді посилання на пошту
    try: # Пробуємо співставити нашого користувача. "Чи правда що це та людина"
        uid = force_str(urlsafe_base64_decode(uidb64)) # Розшифровуємо юід яке відправляли зашифроване
        user = CustomUser.objects.get(pk=uid) # Перевіряємо чи є такий в нашій БД
    except (TypeError, ValueError, OverflowError, CustomUser.DoesNotExist):
        user = None # Якщо нема то так і записуємо

    # Якщо користувач є і перевіряємо користувача і його токен, якщо вони співпадають
    if user is not None and default_token_generator.check_token(user, token):
        if request.method == 'POST':
            form = PasswordResetConfirmForm(request.POST)
            if form.is_valid():
                user.set_password(form.cleaned_data['new_password1']) # Встановлюємо новий пароль, який користувач ввів
                user.save() # Зберігаємо користувача
                messages.success(request, 'Ваш пароль змінено успішно!') # Вивід повідомлення користувачу
                return render(request, 'users/password_reset_complete.html') # Повертаємо сторінку з успішним повідомленням
        else:
            form = PasswordResetConfirmForm() # На початкову сторінку, зарендеримо сторінку і форми
        return render(request, 'users/password_reset_confirm.html', {'form': form, 'validlink': True})
    else:
        # Якщо користувач не знайшовся. Якщо валід лінк фалсе виведемо повідомлення що посилання не валідне
        return render(request, 'users/password_reset_confirm.html', {'validlink': False})

@login_required
def account_activation_request(request):
    if request.method == 'POST': # Жмемо кнопку
            email = request.user.email # Беремо пошту
            user = request.user
            if user: # Якщо такий користувач існує
                if user.email_confirmed:
                    messages.info(request, "Email вже підтверджено.")
                    return redirect('users:profile')


                logging.info(f'Attempting to send acctivation email to {email}, for user id {user.pk}') # Логуємо початок
                send_account_activation_email.delay(email, user.pk) # Запускаємо таску на пошту, передаючи емейл і ід користувача
                messages.success(request, f'Лист активації акаунта надіслано на пошту {email}. Перевірте свою пошту та перейдіть за посиланням в листі')
                # Повідомлення відправлено очікуйте для користувача
                return redirect('users:profile')
            else:
                messages.warning(request, 'Не знайдено акаунта для цієї пошти.') # Нема акаунта повідомлення
    return redirect('users:profile')


def account_activation_confirm(request, uidb64, token):
    # Приймаємо запит, юідб64 і токен який є в тасці. Перейшов по посиланню, ми по цьому посиланню приймаємо ці 2 елемента
    # Які згенеровані для користувача і відправлені в вигляді посилання на пошту
    try:  # Пробуємо співставити нашого користувача. "Чи правда що це та людина"
        uid = force_str(urlsafe_base64_decode(uidb64))  # Розшифровуємо юід яке відправляли зашифроване
        user = CustomUser.objects.get(pk=uid)  # Перевіряємо чи є такий в нашій БД
    except (TypeError, ValueError, OverflowError, CustomUser.DoesNotExist):
        user = None  # Якщо нема то так і записуємо

    # Якщо користувач є і перевіряємо користувача і його токен, якщо вони співпадають
    if user is not None and account_activation_token.check_token(user, token):
                if user.email_confirmed:
                    messages.info(request, "Email вже підтверджено.")
                    return redirect('users:profile')

                user.email_confirmed = True  # Вказуємо що пошта не активована
                user.save(update_fields=["email_confirmed"])  # Зберігаємо користувача
                messages.success(request, 'Акаунт успішно активований!')  # Вивід повідомлення користувачу
                return redirect('users:profile')  # Повертаємо сторінку з успішним повідомленням
    else:
        # Якщо користувач не знайшовся. Якщо валід лінк фалсе виведемо повідомлення що посилання не валідне
        return render(request, 'users/password_reset_confirm.html', {'validlink': False})
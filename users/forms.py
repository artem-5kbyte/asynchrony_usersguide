from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth import get_user_model, authenticate
from django.core.validators import RegexValidator
from django.utils.html import strip_tags

User = get_user_model() # Бере з налаштувань AUTH_USER_MODEL і працює разом з ним

class CustomUserCreationForm(UserCreationForm):
    email = forms.EmailField(required=True, max_length=150,
                             widget=forms.EmailInput(attrs={'class': 'input-register form-control', 'placeholder':'Ваш email'}))
    username = forms.CharField(required=True, max_length=150,
                               widget=forms.TextInput(attrs={'class': 'input-register form-control', 'placeholder':'Ваш тег'}))
    first_name = forms.CharField(required=True, max_length=150,
                                 widget=forms.TextInput(attrs={'class': 'input-register form-control', 'placeholder':'Ім`я'}))
    last_name = forms.CharField(required=True, max_length=150,
                                widget=forms.TextInput(attrs={'class': 'input-register form-control', 'placeholder':'Прізвище'}))
    password1 = forms.CharField(required=True, max_length=150,
                                widget=forms.PasswordInput(attrs={'class': 'input-register form-control', 'placeholder':'Пароль'}))
    password2 = forms.CharField(required=True, max_length=150,
                                widget=forms.PasswordInput(attrs={'class': 'input-register form-control', 'placeholder':'Повторіть пароль'}))
    marketing_consent1 = forms.BooleanField(required=False,
                                            label='Підписатись на розсилку пропозицій',
                                            widget=forms.CheckboxInput(attrs={'class': 'checkbox-input-register'}))
    marketing_consent2 = forms.BooleanField(required=False,
                                            label='Підписатись на персоналізовану розсилку пропозицій',
                                            widget=forms.CheckboxInput(attrs={'class': 'checkbox-input-register'}))

    class Meta:
        model = User
        fields = ('email', 'first_name', 'last_name', 'username', 'password1', 'password2', 'marketing_consent1', 'marketing_consent2')

    def clean_email(self): # Метод для перехоплення тих емейлів які вже були зареєстровані
        email = self.cleaned_data.get('email') # Берем емейл який користувач вписав
        if User.objects.filter(email=email).exists(): # Якщо емейл знаходиться в бд
            raise forms.ValidationError("Цей email вже використовується.")
        return email

    def save(self, commit=True): # перевизначений метод save(). commit=True (за замовчуванням) → об’єкт збережеться в базу. commit=False → об’єкт створиться, але не буде збережений
        user = super().save(commit=False) # викликається стандартний save() батьківського класу (ModelForm). commit=False означає: створити об’єкт user, але не зберігати його ще в БД. Це робиться, щоб мати змогу дописати поля перед збереженням.
        user.marketing_consent1 = self.cleaned_data.get('marketing_consent1') # це перевірені та очищені дані з форми. Значення з чекбоксів / полів форми записуються в модель user
        user.marketing_consent2 = self.cleaned_data.get('marketing_consent2') #
        if commit: #
            user.save() # об’єкт реально зберігається в базу даних
        return user # Повертається об’єкт user (збережений або ні — залежить від commit).

class CustomUserLoginForm(AuthenticationForm):
    username = forms.CharField(required=True, max_length=150, label='Email',
                               widget=forms.TextInput(attrs={'autofocus': True, 'class': 'input-register form-control', 'placeholder':'Email'}))
    password = forms.CharField(required=True, max_length=150, label='Password',
                               widget=forms.PasswordInput(attrs={'autofocus': True, 'class': 'input-register form-control', 'placeholder':'Пароль'}))

    def clean(self):
        email = self.cleaned_data.get('username') # Беремо емейл з форми
        password = self.cleaned_data.get('password') # Беремо емейл з форми

        if email and password: # Перевіряємо, що обидва поля заповнені
            self.user_cache = authenticate(self.request, username=email, password=password) # Пробуємо знайти користувача з такими даними
            if self.user_cache is None: # Якщо користувача не знайдено
                raise forms.ValidationError('Невірний email або пароль користувача.')
            elif not self.user_cache.is_active: # Якщо акаунт вимкнений
                raise forms.ValidationError('Ваш акаунт неактивний!')
        return self.cleaned_data # Повертаємо очищені та перевірені дані

class CustomUserUpdateForm(forms.ModelForm):
    phone = forms.CharField(required=False,
                            validators=[RegexValidator(r'^\+?1?\d{9,15}$', "Введіть правильний номер телефону")],
                            widget=forms.TextInput(attrs={'class': 'input-register form-control', 'placeholder':'Номер телефону'}))
    username = forms.CharField(required=True,
                               max_length=150,
                               widget=forms.TextInput(attrs={'class': 'input-register form-control', 'placeholder': 'Ваш тег'}))
    first_name = forms.CharField(required=True,
                                 max_length=150,
                                 widget=forms.TextInput(attrs={'class': 'input-register form-control', 'placeholder': 'Ім`я'}))
    last_name = forms.CharField(required=True,
                                max_length=150,
                                widget=forms.TextInput(attrs={'class': 'input-register form-control', 'placeholder': 'Прізвище'}))
    email = forms.EmailField(required=True,
                             max_length=150,
                             widget=forms.EmailInput(attrs={'class': 'input-register form-control', 'placeholder': 'Ваш email'}))

    class Meta:
        model = User
        fields = ('first_name', 'last_name','phone', 'username',  'email',
                  'address1', 'address2', 'city', 'country', 'province', 'postal_code', 'marketing_consent1', 'marketing_consent2')
        # Перелік полів моделі User, які будуть відображені та оброблені у формі

        widgets = {
            'email': forms.EmailInput(attrs={'class': 'input-register form-control', 'placeholder': 'Ваш email'}),
            'first_name': forms.TextInput(attrs={'class': 'input-register form-control', 'placeholder': 'Ім`я'}),
            'last_name': forms.TextInput(attrs={'class': 'input-register form-control', 'placeholder': 'Прізвище'}),
            'username': forms.TextInput(attrs={'class': 'input-register form-control', 'placeholder': 'Тег'}),
            'phone': forms.TextInput(attrs={'class': 'input-register form-control', 'placeholder': 'Номер телефону'}),
            'address1': forms.TextInput(attrs={'class': 'input-register form-control', 'placeholder': 'Адреса 1'}),
            'address2': forms.TextInput(attrs={'class': 'input-register form-control', 'placeholder': 'Адреса 2'}),
            'city': forms.TextInput(attrs={'class': 'input-register form-control', 'placeholder': 'Місто'}),
            'province': forms.TextInput(attrs={'class': 'input-register form-control', 'placeholder': 'Область'}),
            'postal_code': forms.TextInput(attrs={'class': 'input-register form-control', 'placeholder': 'Поштовий код'}),
        }
    def clean_email(self):
        email = self.cleaned_data.get('email') # Беремо email, який користувач ввів у форму
        if email and User.objects.filter(email=email).exclude(id=self.instance.id).exists():
            # Перевіряємо, чи існує інший користувач з таким email,
            # але виключаємо поточного користувача (self.instance.id)
            raise forms.ValidationError("Цей email вже використовується.")
        return email
        # Повертаємо перевірений email

    def clean(self):
        cleaned_data = super().clean()
        # Отримуємо всі перевірені дані після стандартної валідації Django
        if not cleaned_data.get('email'): # Якщо email не передали або він порожній
            cleaned_data['email'] = self.instance.email # Беремо email з існуючого користувача (щоб не затерти його)

            for field in ['phone', 'address1', 'address2', 'city', 'country', 'province', 'postal_code']: # Проходимося по текстових полях
                if cleaned_data.get(field): # Якщо поле заповнене
                    cleaned_data[field] = strip_tags(cleaned_data[field])
                    # Видаляємо HTML-теги (захист від XSS)
        return cleaned_data
        # Повертаємо очищені дані

class PasswordResetRequestForm(forms.Form):
    email = forms.EmailField(required=True, max_length=150,
                             widget=forms.EmailInput(
                                 attrs={'class': 'input-register form-control', 'placeholder': 'Ваш email'}))


class PasswordResetConfirmForm(forms.Form):
    new_password1 = forms.CharField(required=True, max_length=150,
                                widget=forms.PasswordInput(
                                    attrs={'class': 'input-register form-control', 'placeholder': 'Пароль'}))
    new_password2 = forms.CharField(required=True, max_length=150,
                                widget=forms.PasswordInput(
                                    attrs={'class': 'input-register form-control', 'placeholder': 'Повторіть пароль'}))

    def clean(self): # Перевизначення вже існуючої функції
        cleaned_data = super().clean() # Виклик батківського методу
        new_password1 = cleaned_data.get('new_password1') #
        new_password2 = cleaned_data.get('new_password2')  # Беремо з очищених полів нові паролі
        if new_password1 and new_password2 and new_password1 != new_password2: # Якщо new_password пустий або 1 не = 2 тоді видаємо помилку
            raise forms.ValidationError('')
        return cleaned_data # Повертаємо для того щоб в подальшому в views могли використовувати для зміни чи звертання в БД щоб змінити пароль користувачу
    
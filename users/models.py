from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.utils.html import strip_tags

class CustomUserManager(BaseUserManager):
    def create_user(self, email, first_name, last_name, username, password=None, **extra_fields): # Поля які будемо використовувати для реєстрації
        if not email:
            raise ValueError('Необхідно вказати email!')

        email = self.normalize_email(email) # Функція для валідації пошти
        user = self.model(email=email, first_name=first_name, username=username, last_name=last_name, **extra_fields)
        #  Створюється юзер, він модель. А модель має в собі поля які користувач ввів
        user.set_password(password) # Вказуємо пароль
        user.save(using=self._db) # Зберігаємо в нашу базу даних
        return user


    # Нам необхідно задати поля для створення супер юзера, бо він видаватиме помилку через те зо потребує дефолтних полів
    def create_superuser(self, email, first_name, last_name, password, username=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        #!  extra_fields це Права користувача /\

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Супер користувач повинен бути is_staff=True.')

        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Супер користувач повинен бути is_superuser=True.')
        if username is None:
            username = email.split('@')[0]
        return self.create_user(email, first_name, username, last_name, password, **extra_fields)


class CustomUser(AbstractUser):
    email = models.EmailField(unique=True, verbose_name='Email', max_length=100)
    first_name = models.CharField(verbose_name='Ім`я', max_length=100)
    last_name = models.CharField(verbose_name='Прізвище', max_length=100)
    username = models.CharField(verbose_name='Нікнейм', max_length=150, unique=True)
    phone = models.CharField(verbose_name='Номер телефону', max_length=15, blank=True, null=True)

    address1 = models.CharField(verbose_name='Адреса', max_length=255, blank=True, null=True) #  null=True щоб в БД була пуста клітинка
    address2 = models.CharField(verbose_name='Вулиця', max_length=255, blank=True, null=True) #  null=True щоб в БД була пуста клітинка
    city = models.CharField(verbose_name='Місто', max_length=255, blank=True, null=True)
    country = models.CharField(verbose_name='Країна', max_length=150, blank=True, null=True)
    province = models.CharField(verbose_name='Область', max_length=255, blank=True, null=True)
    postal_code = models.CharField(verbose_name='Поштовий код', max_length=15, blank=True, null=True)
    marketing_consent1 = models.BooleanField(default=False) # Розсилка на рекламу
    marketing_consent2 = models.BooleanField(default=False)

    email_confirmed = models.BooleanField(default=False)

    """
     За замовчуванням якщо ми навіть створимо модель, Джанго потребуватиме нікнейм для реєстрації 
     Для того щоб зробити реєстрацію по пошті
     """

    objects = CustomUserManager() # Ініціалізуємо для

    USERNAME_FIELD = 'email' # Необхідно взяти юзернейм і помііняти на емейл, Щоб джанго в своїй моделі замінив юзернейм на емейл який нам необхіно використати
    REQUIRED_FIELDS = ['first_name', 'last_name'] # Посторонні поля які будуть використовувати для реєстрації (Ми їх хлчемо бачити в реєстрації)

    def __str__(self):
        return self.email

    def clean(self):
        # Метод clean() у моделі викликається перед збереженням об'єкта
        for field in ['phone', 'address1', 'address2', 'city', 'country', 'province',
                      'postal_code']:  # Проходимося по всіх полях, які можуть містити текст
            value = getattr(self, field)
            # Отримуємо значення поля з об'єкта моделі
            if value:
                # Якщо поле не порожнє
                setattr(self, field, strip_tags(value))
                # Очищаємо значення від HTML і записуємо назад у модель


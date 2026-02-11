# Логіка роботи відправки листів
from celery import shared_task
from django.core.mail import send_mail # Стандартна функція від джанго для розсилки
from django.conf import settings
import logging

logger = logging.getLogger(__name__) # Логування щоб бачити в терміналі чи відправився лист

@shared_task # Передаємо завдання на виконання celery і брокером між цим повіомленням і самим селері виступає редіс. Через нього видаємо і отримуємо результат
def send_welcome_email(email, first_name): #
    subject = 'Ласкаво просимо на нашу платформу!' # Назва, тема
    # Вітальне повідомлення
    message = f""" 
    Вітаємо {first_name}!
    
    Дякуємо, що ви приєдналися до нашої платформи. Ми раді бачити Вас тут!
    
    З найкращими побажаннями,
    Адміністрація!
    """

    html_message = f"""
    <h1>Вітаємо, {first_name}!!</h1>
    <p>Дякуємо, що ви приєдналися до нашої платформи. Ми раді бачити Вас тут!</p>
    <p>З найкращими побажаннями,<br>Адміністрація!</p>
    """
    # Пробуємо відправити наш лист
    try:
        send_mail( #
            subject, # Заголовок
            message, # Саме повідомлення
            settings.DEFAULT_FROM_EMAIL, # Беремо нашу пошту з налаштувань
            [email], # Сам емейл, кому відправити
            fail_silently=False,
            html_message=html_message, # ГТМЛ повідомлення
        )
        logger.info(f'Welcome email sent {email}, - {first_name}')

    except Exception as e: # В разі невдачі виводимо помилку в термінал
        logger.error(f'Welcome email - {email} failed: {str(e)}')
        raise


@shared_task
def send_account_activation_email(email, user_id):
    from .models import CustomUser
    from django.urls import reverse # Для урл-ок
    from .tokens import account_activation_token
    from django.utils.http import urlsafe_base64_encode # Для генерації спец ключа який буде відправлений користувачу і де згенерується посилання
    from django.utils.encoding import force_bytes # унікальне для користувача для відновлення пароля

    logger.info(f'Starting activation email for {email}, user_id: {user_id}') # Логуємо початок
    try: # Пробуємо
        user = CustomUser.objects.get(pk=user_id) # Беремо користувача, який це відправив

        if not user:
            logger.warning("User not found")
            return

        if user.email_confirmed:
            logger.info("User already activated")
            return

        token = account_activation_token.make_token(user) # Робимо токен унікальний на основі користувача
        uid = urlsafe_base64_encode(force_bytes(user.pk)) # Робимо унікальне юід. Кодуємо стандартною джанго функцією. Кодуємо користувача
        # Створюємо ресет посилання. Домен, Посилання відновлення пароля, унікальний ключ. Зашифроване юід і створений токен
        # 2 унікальних ключа з яких згенерується унікальне посилання для кожного користувача і ніколи в житі не буде повторюватись,


        activation_url = f"{settings.SITE_URL}{reverse('users:account_activation_confirm', kwargs={'uidb64': uid, 'token': token})}"

        # Надсилаємо повідомлення
        subject = 'Активація акаунту'  # Назва, тема
        # Вітальне повідомлення
        message = f""" 
            Вітаємо {user.first_name or user.email}!
    
            Натисніть на посилання для активації вашого акаунту {user.email}
            {activation_url}
            
            Якщо ви не робили запиту, ігноруйте це повідомлення.
            
            З найкращими побажаннями,
            Адміністрація!
            """

        html_message = f"""
            <h1>Активація акаунту</h1>
            <h1>Вітаємо {user.first_name or user.email}!</h1>
            <p>Натисніть на посилання для активації вашого акаунту <b> {user.email} </b></p>
            <a href="{activation_url}">{activation_url}</a>
            <p>Якщо ви не робили запиту, ігноруйте це повідомлення.</p>
            <p>З найкращими побажаннями,<br>Адміністрація!</p>
            """
        send_mail(  #
            subject,  # Заголовок
            message,  # Саме повідомлення
            settings.DEFAULT_FROM_EMAIL,  # Беремо нашу пошту з налаштувань
            [email],  # Сам емейл, кому відправити
            fail_silently=False,
            html_message=html_message,  # ГТМЛ повідомлення
        )
        logger.info(f'Activation email sent {email}')

    except Exception as e: # В разі невдачі виводимо помилку в термінал
        logger.error(f'Activation email - {email} failed: {str(e)}')
        raise

@shared_task
def send_password_reset_email(email, user_id):
    from .models import CustomUser
    from django.urls import reverse  # Для урл-ок
    from django.contrib.auth.tokens import default_token_generator
    from django.utils.http import urlsafe_base64_encode  # Для генерації спец ключа який буде відправлений користувачу і де згенерується посилання
    from django.utils.encoding import force_bytes  # унікальне для користувача для відновлення пароля

    logger.info(f'Starting password reset email for {email}, user_id: {user_id}')  # Логуємо початок
    try:  # Пробуємо
        user = CustomUser.objects.get(pk=user_id)  # Беремо користувача, який це відправив
        token = default_token_generator.make_token(user)  # Робимо токен унікальний на основі користувача
        uid = urlsafe_base64_encode(force_bytes(user.pk))  # Робимо унікальне юід. Кодуємо стандартною джанго функцією. Кодуємо користувача
        # Створюємо ресет посилання. Домен, Посилання відновлення пароля, унікальний ключ. Зашифроване юід і створений токен
        # 2 унікальних ключа з яких згенерується унікальне посилання для кожного користувача і ніколи в житі не буде повторюватись,

        reset_url = f"{settings.SITE_URL}{reverse('users:password_reset_confirm', kwargs={'uidb64': uid, 'token': token})}"

        # Надсилаємо повідомлення
        subject = 'Запит для скидання пароля'  # Назва, тема
        # Вітальне повідомлення
        message = f""" 
            Вітаємо {user.first_name or user.email}!

            Натисніть на посилання для скидання пароля на вашому акаунті {user.email}
            {reset_url}

            Якщо ви не робили запиту, ігноруйте це повідомлення.

            З найкращими побажаннями,
            Адміністрація!
            """

        html_message = f"""
            <h1>Запит для скидання пароля</h1>
            <h1>Вітаємо {user.first_name or user.email}!</h1>
            <p>Натисніть на посилання для скидання пароля на вашому акаунті <b> {user.email} </b></p>
            <a href="{reset_url}">{reset_url}</a>
            <p>Якщо ви не робили запиту, ігноруйте це повідомлення.</p>
            <p>З найкращими побажаннями,<br>Адміністрація!</p>
            """
        send_mail(  #
            subject,  # Заголовок
            message,  # Саме повідомлення
            settings.DEFAULT_FROM_EMAIL,  # Беремо нашу пошту з налаштувань
            [email],  # Сам емейл, кому відправити
            fail_silently=False,
            html_message=html_message,  # ГТМЛ повідомлення
        )
        logger.info(f'Reset password email sent {email}')

    except Exception as e:  # В разі невдачі виводимо помилку в термінал
        logger.error(f'Reset password email - {email} failed: {str(e)}')
        raise
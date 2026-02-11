# Тут опишемо логіку створення токена для активації пошти

from django.contrib.auth.tokens import PasswordResetTokenGenerator

# Створюємо СВІЙ генератор токенів для активації email.
# Наслідуємося від PasswordResetTokenGenerator,
# щоб не писати складну криптографію самостійно.

class EmailActivationTokenGenerator(PasswordResetTokenGenerator): #

    # Цей метод визначає КОЛИ токен має ставати невалідним.
    # Django бере цей рядок → хешує → створює токен.
    def _make_hash_value(self, user, timestamp): #
        # Формуємо рядок з унікальних даних користувача.
        # Якщо БУДЬ-ЩО з цього зміниться —
        # старий токен автоматично перестане працювати.
        return f'{user.pk}{user.email}{timestamp}{user.email_confirmed}' #


# user.pk
# → робить токен унікальним для кожного користувача

# user.email
# → якщо користувач змінить email,
#   старий activation-лінк стане невалідним

# timestamp
# → відповідає за строк життя токена

# user.email_confirmed
# → після підтвердження пошти значення зміниться на True,
#   hash стане іншим і токен більше не спрацює


# Створюємо екземпляр генератора.
# Саме його будемо використовувати у коді:
# account_activation_token.make_token(user)
# account_activation_token.check_token(user, token)
account_activation_token = EmailActivationTokenGenerator()
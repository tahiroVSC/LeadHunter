from apps.users.models import CustomUser

def update_balance(user_id, amount):
    try:
        user = CustomUser.objects.get(id=user_id)
        user.balance += amount
        user.save()
        return True
    except CustomUser.DoesNotExist:
        return False
from django.contrib.auth.decorators import user_passes_test



def admin_required(view_func):
    return user_passes_test(lambda u: u.is_authenticated and (u.is_superuser or u.groups.filter(name='Admin').exists()), login_url='login')(view_func)


def sales_manager_required(view_func):
    return user_passes_test(lambda u: u.is_authenticated and u.groups.filter(name='Sales Manager').exists(), login_url='login')(view_func)


def stock_manager_required(view_func):
    return user_passes_test(lambda u: u.is_authenticated and u.groups.filter(name='Stock Manager').exists(), login_url='login')(view_func)
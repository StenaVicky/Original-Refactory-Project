from django.contrib.auth.decorators import user_passes_test



def admin_required(view_func):
    return user_passes_test(
        lambda u: u._superuser or u.groups.filter(name='admin').exists()
    )(view_func)


def sales_manager_required(view_func):
    return user_passes_test(
        lambda u: u.groups.filter(name='sales_manager').exists()

    )(view_func)



def stock_manager_required(view_func):
    return user_passes_test(
        lambda u: u.group.filter(name='stock_manager').exists()

    )(view_func)
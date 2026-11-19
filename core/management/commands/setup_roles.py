from django.contrib.auth.models import Group, Permission
from django.core.management.base import BaseCommand


ROLE_PERMISSIONS = {
    'Product manager': {
        ('catalog', f'{action}_{model}')
        for model in ('category', 'product', 'productvariant', 'productimage')
        for action in ('add', 'change', 'delete', 'view')
    },
    'Inventory manager': {
        ('inventory', 'view_stock'), ('inventory', 'change_stock'),
        ('inventory', 'adjust_stock'), ('inventory', 'view_stockmovement'),
    },
    'Order manager': {
        ('orders', 'view_order'), ('orders', 'view_orderitem'),
        ('orders', 'view_orderstatushistory'), ('orders', 'transition_order'),
        ('inventory', 'view_stock'), ('inventory', 'view_stockmovement'),
    },
}


class Command(BaseCommand):
    help = 'Create or refresh FORM staff role groups and their permissions.'

    def handle(self, *args, **options):
        for name, required in ROLE_PERMISSIONS.items():
            group, _ = Group.objects.get_or_create(name=name)
            permissions = list(Permission.objects.filter(
                content_type__app_label__in={app for app, _ in required},
                codename__in={code for _, code in required},
            ))
            found = {(permission.content_type.app_label, permission.codename) for permission in permissions}
            missing = required - found
            if missing:
                raise RuntimeError(f'Missing permissions for {name}: {sorted(missing)}')
            group.permissions.set(
                permission for permission in permissions
                if (permission.content_type.app_label, permission.codename) in required
            )
            self.stdout.write(f'{name}: {len(required)} permissions')

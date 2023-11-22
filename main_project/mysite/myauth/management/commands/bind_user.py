from django.contrib.auth.models import User, Group, Permission
from django.core.management import BaseCommand


class Command(BaseCommand):
    def handle(self, *args, **options):
        user = User.objects.get()
        group, created = Group.objects.get_or_create(
            name='profile_manager'
        )
        permission_profile = Permission.objects.get()
        permission_logentry = Permission.objects.get()

        group.permissions.add(permission_profile)

        user.groups.add(group)

        user.user_permissions.add(permission_logentry)

        group.save()
        user.save()
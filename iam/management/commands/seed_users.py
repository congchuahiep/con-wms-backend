from django.core.management.base import BaseCommand

from iam.models import Role, User


class Command(BaseCommand):
    help = "Tạo 4 user mẫu (1 mỗi role) để test"

    def handle(self, *_args, **_options):
        users_data = [
            {"email": "admin@gmail.com", "role": Role.ADMIN},
            {"email": "thukho@gmail.com", "role": Role.STOREKEEPER},
            {"email": "chunhiem@gmail.com", "role": Role.SUPERVISOR},
            {"email": "ketoan@gmail.com", "role": Role.ACCOUNTANT},
        ]

        password = "Password123!"

        for data in users_data:
            user, created = User.objects.get_or_create(
                email=data["email"],
                defaults={
                    "role": data["role"],
                    "is_staff": data["role"] == Role.ADMIN,
                    "is_superuser": data["role"] == Role.ADMIN,
                },
            )
            if created:
                user.set_password(password)
                user.save()
                self.stdout.write(
                    self.style.SUCCESS(f"Created: {user.email} ({user.role})")
                )
            else:
                self.stdout.write(f"Exists: {user.email}")

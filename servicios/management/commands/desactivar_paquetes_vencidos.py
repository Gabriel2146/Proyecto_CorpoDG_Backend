from django.core.management.base import BaseCommand
from django.utils import timezone

from servicios.models import PaqueteTuristico


class Command(BaseCommand):
    help = (
        "Sincroniza el estado de los paquetes turísticos según su fecha "
        "'precio_aplica_hasta': desactiva los vencidos y reactiva los que "
        "vuelven a estar vigentes."
    )

    def handle(self, *args, **options):
        hoy = timezone.localdate()
        desactivados, reactivados = PaqueteTuristico.sincronizar_vigencia()
        self.stdout.write(
            self.style.SUCCESS(
                f"[{hoy}] Paquetes desactivados: {desactivados} | "
                f"reactivados: {reactivados}"
            )
        )

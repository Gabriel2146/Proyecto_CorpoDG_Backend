from django.test import TestCase
from .chatbot import _build_accion


class BuildAccionTest(TestCase):

    def test_vuelos_live_retorna_accion_redirect(self):
        accion = _build_accion("buscar_vuelos_live", {
            "origen": "UIO",
            "destino": "MIA",
            "fecha_salida": "2025-08-15",
            "adultos": 2,
        })
        self.assertEqual(accion["tipo"], "redirect_vuelos")
        self.assertEqual(accion["path"], "/vuelos/resultados")
        self.assertEqual(accion["params"]["origin"], "UIO")
        self.assertEqual(accion["params"]["destination"], "MIA")
        self.assertEqual(accion["params"]["date"], "2025-08-15")
        self.assertEqual(accion["params"]["adults"], 2)
        self.assertIn("label", accion)

    def test_detalle_paquete_retorna_accion_redirect(self):
        accion = _build_accion("get_detalle_paquete", {"paquete_id": 42})
        self.assertEqual(accion["tipo"], "redirect_paquete")
        self.assertEqual(accion["path"], "/paquetes/42")
        self.assertEqual(accion["params"], {})
        self.assertIn("label", accion)

    def test_otras_tools_retornan_none(self):
        self.assertIsNone(_build_accion("get_paquetes", {}))
        self.assertIsNone(_build_accion("get_regiones", {}))
        self.assertIsNone(_build_accion("get_vuelos", {"origen": "UIO"}))
        self.assertIsNone(_build_accion("get_aerolineas", {}))

    def test_vuelos_con_fecha_regreso(self):
        accion = _build_accion("buscar_vuelos_live", {
            "origen": "GYE",
            "destino": "MAD",
            "fecha_salida": "2025-09-01",
            "adultos": 1,
            "fecha_regreso": "2025-09-15",
        })
        self.assertEqual(accion["params"]["return_date"], "2025-09-15")
        self.assertEqual(accion["params"]["tipoViaje"], "idaVuelta")

    def test_vuelos_sin_fecha_regreso_tipo_solo_ida(self):
        accion = _build_accion("buscar_vuelos_live", {
            "origen": "UIO",
            "destino": "MIA",
            "fecha_salida": "2025-08-15",
            "adultos": 1,
        })
        self.assertEqual(accion["params"].get("tipoViaje"), "soloIda")

    def test_detalle_paquete_sin_id_retorna_none(self):
        self.assertIsNone(_build_accion("get_detalle_paquete", {}))
        self.assertIsNone(_build_accion("get_detalle_paquete", {"paquete_id": 0}))

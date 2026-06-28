from app.services.route_service import RouteService


class OptimizeUseCase:
    def __init__(self, service: RouteService | None = None):
        self.service = service or RouteService()

    def execute(
        self,
        stops: list[dict],
        vehicles: list[dict],
        use_demo: bool = True,
    ) -> dict:
        if use_demo:
            return self.service.optimize_demo()
        return self.service.optimize(stops, vehicles, use_demo=False)

    def demo_metrics(self) -> dict:
        return self.service.demo_metrics()

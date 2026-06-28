from abc import ABC, abstractmethod


class RouteOptimizerPort(ABC):
    @abstractmethod
    def optimize(self, stops: list[dict], vehicles: list[dict], use_demo: bool = True) -> dict:
        raise NotImplementedError

    @abstractmethod
    def demo_metrics(self) -> dict:
        raise NotImplementedError

class LogConfig:
    def __init__(self, name: str, period_in_ms: int = 100):
        self.name = name
        self.period_in_ms = period_in_ms
        self.variables = []

    def add_variable(self, name: str, fmt: str):
        self.variables.append((name, fmt))


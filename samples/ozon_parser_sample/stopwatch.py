import time

class Stopwatch:
    def __init__(self):
        self._start_time = None
        self._elapsed = 0.0

    def start(self):
        """Запустить секундомер."""
        if self._start_time is not None:
            print("The stopwatch has already started.")
            return
        self._start_time = time.perf_counter()

    def stop(self):
        """Остановить секундомер и вернуть время."""
        if self._start_time is None:
            print("The stopwatch has not started.")
            return
        self._elapsed += time.perf_counter() - self._start_time
        self._start_time = None

    def reset(self):
        """Сбросить секундомер."""
        self._start_time = None
        self._elapsed = 0.0

    def elapsed_time(self):
        """Получить время, прошедшее с момента запуска."""
        if self._start_time is not None:
            return self._elapsed + (time.perf_counter() - self._start_time)
        return self._elapsed

    def __str__(self):
        """Вернуть строковое представление прошедшего времени."""
        return f"{self.elapsed_time():.4f} second"

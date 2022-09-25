from typing import Callable


class Message(list):
    def subscribe(self, subscriber: Callable) -> None:
        self.append(subscriber)

    def publish(self, *args, **kwargs) -> None:
        for subscriber in self:
            subscriber(*args, **kwargs)

    def __call__(self, *args, **kwargs) -> None:
        self.publish(*args, **kwargs)

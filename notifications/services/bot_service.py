from abc import abstractmethod

from base.singletons import SingletonABCMeta


class BaseBotService(metaclass=SingletonABCMeta):
    @abstractmethod
    def send_notification(
        self, chat_id: int | str, text: str, **kwargs
    ) -> None:
        pass

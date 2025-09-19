from abc import ABC, abstractmethod


class BaseBotService(ABC):
    @abstractmethod
    def send_notification(self, chat_id: int | str, text: str, **kwargs) -> None:
        pass
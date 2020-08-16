import abc
from interfaces.ICallback import ICallback


class IConsumer(abc.ABC):
    
    @abc.abstractmethod
    def _build_connection(self):
        raise NotImplementedError
    
    @abc.abstractmethod
    def start(self, callback:ICallback):
        raise NotImplementedError
    
    @abc.abstractmethod
    def stop(self):
        raise NotImplementedError
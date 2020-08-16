import abc


class ICallback(abc.ABC):
    
    @abc.abstractmethod
    def callback(self, request:str):
        raise NotImplementedError
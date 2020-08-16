import abc


class IProducer(abc.ABC):
    
    @abc.abstractmethod
    def _build_connection(self):
        raise NotImplementedError
    
    @abc.abstractmethod
    def call(self):
        raise NotImplementedError
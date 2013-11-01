from abc import ABCMeta, abstractmethod

class GenericSampler(object):
    __metaclass__ = ABCMeta

    @abstractmethod
    def init(self):
        pass

    @abstractmethod
    def next(self):
    '''returns next sample'''
        pass

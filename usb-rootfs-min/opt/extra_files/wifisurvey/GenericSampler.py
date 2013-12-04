from abc import ABCMeta, abstractmethod

class GenericSampler(object):
    __metaclass__ = ABCMeta

    #returns next sample
    @abstractmethod
    def next(self):
        pass


class TestSampler(GenericSampler):
  def __init__(self):
    self.n = 0
    pass

  def next(self):
    self.n += 1
    return {'n':self.n}

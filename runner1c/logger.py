
import abc
import runner1c.common as common


class Logger(abc.ABC):
    def __init__(self, **kwargs):
        self.parent = kwargs.get('parent', None)
        self._logger = kwargs.get('logger', None)
        if self._logger is None:
            part_name = []
            if self.parent is not None:
                part_name.append(self.parent.get_logger_name())
                logger_handlers = self.parent.get_logger_handlers()
            else:
                logger_handlers = kwargs.get('logger_handlers', None)
            part_name.append(self.name)
            self._logger = common.get_logger('_'.join(part_name), kwargs['arguments'].debug, logger_handlers)
    @property
    def name(self):
        return self.__class__.__name__

    def get_logger_name(self):
        return self._logger.name

    def get_logger_handlers(self):
        return self._logger.handlers

    def debug(self, msg, *args):
        self._logger.debug(msg, *args)

    def error(self, msg, *args):
        self._logger.error(msg, *args)
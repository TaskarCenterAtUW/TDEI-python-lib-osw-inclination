import logging


class Logger:
    logger = None

    @staticmethod
    def configure_logger():
        if Logger.logger is None:
            logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s')
            Logger.logger = logging.getLogger('INCLINATION SERVICE ')
            Logger.logger.setLevel(logging.INFO)
        return Logger.logger

    @staticmethod
    def info(message):
        Logger.configure_logger().info(message)

    @staticmethod
    def error(message):
        Logger.configure_logger().error(message)

    @staticmethod
    def warning(message):
        Logger.configure_logger().warning(message)



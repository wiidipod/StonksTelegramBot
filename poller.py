import telegram_service
import logging
import time
import sys

# Set up logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)


def wait_for_network(max_wait_seconds=300, check_interval=10):
    """Wait for network connectivity before starting the bot."""
    import socket

    start_time = time.time()
    while time.time() - start_time < max_wait_seconds:
        try:
            # Try to resolve Telegram's API hostname
            socket.gethostbyname('api.telegram.org')
            logger.info("Network connectivity confirmed")
            return True
        except socket.gaierror:
            elapsed = int(time.time() - start_time)
            logger.warning(f"Network not ready yet (waited {elapsed}s), retrying in {check_interval}s...")
            time.sleep(check_interval)

    logger.error(f"Network not available after {max_wait_seconds}s")
    return False


if __name__ == '__main__':
    logger.info("Starting Telegram bot poller...")

    # Wait for network to be available
    if not wait_for_network():
        logger.error("Cannot start bot without network connectivity")
        sys.exit(1)

    # Add a small additional delay to ensure network is stable
    time.sleep(5)

    try:
        application = telegram_service.get_handling_application()
        logger.info("Starting polling...")
        application.run_polling(
            allowed_updates=None,
            drop_pending_updates=True,
            close_loop=False
        )
    except Exception as e:
        logger.error(f"Failed to start bot: {e}", exc_info=True)
        sys.exit(1)


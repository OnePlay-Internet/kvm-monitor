import logging
import os

MONITORING_INTERVAL = 30

if not os.path.exists('./logs'):
    os.makedirs('logs')

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("./logs/system_monitor.log"),
        logging.StreamHandler()
    ]
)

# Create a logger instance
logger = logging.getLogger(__name__)
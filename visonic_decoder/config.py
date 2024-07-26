"""Runner config."""

import logging


PROXY_MODE = True
LOG_LEVEL = logging.INFO
LOG_TO_FILE = True
LOG_FILES_TO_KEEP = 10

# Level of messagestobe logged.
# 1 just decoded messages
# 2 same as 1 plus raw message
# 3 same as 2 plus decoder info
# 4 same as 3 plus structured message, paged messages
# 5 same as 4 plus powerlink message decoded, ACKs, forwarding info, keep-alives
MESSAGE_LOG_LEVEL = 2

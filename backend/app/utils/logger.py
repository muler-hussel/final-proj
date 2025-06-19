import logging
import os
import subprocess
from logging.handlers import TimedRotatingFileHandler

# Logging setting, aiming at recording ai response
# Stored at /logs/app.log.{datetime}
# Log into a new file every week
# Also print in console
LOG_DIR = "logs"
os.makedirs(LOG_DIR, exist_ok=True)

def get_git_commit_hash():
  try:
    return subprocess.check_output(["git", "rev-parse", "HEAD"]).decode("utf-8").strip()
  except Exception:
    return "unknown"

commit_hash = get_git_commit_hash()

class CommitFilter(logging.Filter):
  def filter(self, record):
    record.commit = commit_hash
    return True

log_file_handler = TimedRotatingFileHandler(
  filename=f"{LOG_DIR}/app.log",
  when="W0", # Monday
  interval=1, # Every week
  encoding="utf-8"
)
log_file_handler.addFilter(CommitFilter())

logging.basicConfig(
  level=logging.INFO,
  format="%(asctime)s - [%(levelname)s] - %(name)s - %(commit)s - %(message)s",
  handlers=[
    log_file_handler,
    logging.StreamHandler() 
  ]
)

logger = logging.getLogger("TravelAI")
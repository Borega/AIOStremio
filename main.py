import json
import asyncio
import httpx
import os
import time
import logging
import bcrypt
from collections import defaultdict
from contextlib import asynccontextmanager

import uvicorn
from cryptography.fernet import Fernet
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel

from routes.api import router
from services.comet import CometService
from services.easynews import EasynewsService
from services.mediafusion import MediaFusionService
from services.torbox import TorboxService
from services.torrentio import TorrentioService
from services.debridio import DebridioService
from services.peerflix import PeerflixService
from services.watchhub import WatchHubService
from utils.cache import get_cache_info
from utils.config import config
from utils.logger import logger

load_dotenv()

logging.getLogger("httpx").setLevel(logging.WARNING)

# Order is reflected in Stremio
streaming_services = [
    service
    for service in [
        WatchHubService(),
        TorboxService() if config.debrid_service.lower() == "torbox" else None,
        TorrentioService() if config.debrid_service is not None else None,
        CometService() if config.debrid_service is not None else None,
        MediaFusionService() if os.getenv("MEDIAFUSION_OPTIONS") else None,
        (
            EasynewsService()
            if os.getenv("EASYNEWS_USERNAME") and os.getenv("EASYNEWS_PASSWORD")
            else None
        ),
        DebridioService() if config.get_addon_debrid_api_key("debridio") != os.getenv("DEBRID_API_KEY") and config.get_addon_debrid_service("debridio") != config.debrid_service else None,
        PeerflixService() if config.debrid_service is not None else None,
    ]
    if service is not None
]

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info(f"Cache Info\nSize: {(await get_cache_info())['total_size_mb']}MB")
    yield

app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

USERS_FILE = "db/users.json"
RATE_LIMIT_MINUTES = 1
MAX_REQUESTS = 30
CACHE_TTL = config.cache_ttl_seconds

ENCRYPTION_KEY = os.getenv("ENCRYPTION_KEY")
if not ENCRYPTION_KEY:
    ENCRYPTION_KEY = Fernet.generate_key()
    logger.warning(
        "No ENCRYPTION_KEY set, a new key will be generated on every restart."
    )
fernet = Fernet(ENCRYPTION_KEY)

rate_limits = defaultdict(list)


class User(BaseModel):
    username: str
    password: str
    proxy_streams: bool = True


class RateLimiter:
    def __init__(self, max_requests: int, window_minutes: int):
        self.max_requests = max_requests
        self.window_minutes = window_minutes

    def is_rate_limited(self, user: str) -> bool:
        now = time.time()
        minute_ago = now - (self.window_minutes * 60)

        # Clean old requests
        rate_limits[user] = [
            req_time for req_time in rate_limits[user] if req_time > minute_ago
        ]

        # Check if rate limited
        if len(rate_limits[user]) >= self.max_requests:
            logger.info(
                f"Rate limit exceeded for user: {user} ({len(rate_limits[user])}/{self.max_requests})"
            )
            return True

        # Add new request
        rate_limits[user].append(now)
        return False


rate_limiter = RateLimiter(MAX_REQUESTS, RATE_LIMIT_MINUTES)


class AdminAuth:
    def __init__(self):
        admin_username = os.getenv("ADMIN_USERNAME")
        admin_password = os.getenv("ADMIN_PASSWORD")

        self.admin_credentials = {
            "username": admin_username,
            "password_hash": bcrypt.hashpw(admin_password.encode(), bcrypt.gensalt()),
        }

    def verify_admin(self, username: str, password: str) -> bool:
        if username != self.admin_credentials["username"]:
            return False
        return bcrypt.checkpw(password.encode('utf-8'), self.admin_credentials["password_hash"])


admin_auth = AdminAuth()

templates = Jinja2Templates(directory="templates")

app.include_router(router)


async def sanity_check():
    logger.info("Performing sanity check...")

    addon_urls = [service.base_url for service in streaming_services]

    logger.info("Addons | Checking addons...")

    for url in addon_urls:
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(url)
                if response.status_code not in [200, 302, 307]:
                    logger.warning(f"Addons | ⚠️ {url} (Status: {response.status_code})")
                else:
                    logger.info(f"Addons | ✅ {url}")
        except (httpx.ReadTimeout, httpx.ConnectTimeout):
            logger.warning(f"Addons | ⚠️ {url} (Timeout)")
            continue
        except Exception as e:
            logger.warning(f"Addons | ⚠️ {url} ({str(e)})")
            continue

    logger.info("Config | Checking config...")

    with open("config.json.example", "r") as f:
        example_config = json.load(f)

    def validate_config_structure(example: dict, current: dict, path: str = ""):
        for key, value in example.items():
            current_path = f"{path}.{key}" if path else key
            if key not in current:
                logger.warning(f"Config | ⚠️ The config is outdated (missing {current_path})")
                exit(1)
            if isinstance(value, dict):
                if not isinstance(current[key], dict):
                    logger.warning(f"Config | ⚠️ The config is malformed (expected dict for {current_path} but got {type(current[key])})")
                    exit(1)
                validate_config_structure(value, current[key], current_path)

    validate_config_structure(example_config, config._config)

    logger.info("Config | ✅ The config is up to date")

    if (
        not config.debrid_service
        and not os.getenv("MEDIAFUSION_OPTIONS")
        and not (os.getenv("EASYNEWS_USERNAME") and os.getenv("EASYNEWS_PASSWORD"))
    ):
        logger.warning("Config | ⚠️ No services configured")
        exit(1)

    if config.debrid_service and not os.getenv("DEBRID_API_KEY"):
        logger.warning("Config | ⚠️ Default debrid service is configured but no API key is set")
        exit(1)

    for service_name in config._config.get("addon_config", {}).keys():
        debrid_service = config.get_addon_debrid_service(service_name)
        debrid_api_key = config.get_addon_debrid_api_key(service_name)
        if service_name == "debridio" and debrid_api_key == os.getenv("DEBRID_API_KEY") and debrid_service != config.debrid_service:
            continue
        if debrid_service == config.debrid_service:
            logger.info(f"Config | *️⃣ Using default debrid service ({debrid_service}) for {service_name}")
        else:
            logger.info(f"Config | *️⃣ Using {debrid_service} for {service_name}")


if __name__ == "__main__":
    asyncio.run(sanity_check())
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8469,
        log_config={
            "version": 1,
            "disable_existing_loggers": False,
            "loggers": {
                "uvicorn.access": {"level": "WARNING"},
            },
        },
    )

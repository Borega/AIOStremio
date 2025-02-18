# AIOStremio

[![commit activity](https://img.shields.io/github/commit-activity/m/stekc/aiostremio)](https://github.com/stekc/aiostremio/commits)
[![last commit](https://img.shields.io/github/last-commit/stekc/aiostremio)](https://github.com/stekc/aiostremio/commits)
[![chat](https://img.shields.io/discord/1178091792504201357?logo=discord&logoColor=white)](https://discord.gg/MkCvXWjeAx)

[![Stremio](https://img.shields.io/badge/Stremio-mediumpurple)](https://stremio.com/)
[![Vidi](https://img.shields.io/badge/Vidi-black)](https://vidi.plomo.se/)
[![Madari](https://img.shields.io/badge/Madari-red)](https://downloads.madari.media/)

AIOStremio combines your favorite Stremio addons into one. Easily sync your setup with friends—changes update for all users without any reconfiguration on their end.

(Note: Not all services allow account sharing, and it may lead to a ban. Consider using [TorBox](https://torbox.app/subscription?referral=fe897519-fa8d-402d-bdb6-15570c60eff2) (referral link), which allows account sharing.)

![Stremio, Android TV, custom formatting applied](https://i.ibb.co/fxgjs5D/simple-on-bestpres-on.png)
<small>*Stremio, on Android TV, with custom formatting applied*</small>

<details>
<summary>More Images</summary>

|                           |         |
|------------------------------------|--------------------|
| <img src="https://i.postimg.cc/2YgCXJ5Y/IMG-3880.png" width="300"> | *Homepage*          |
| <img src="https://i.postimg.cc/npGZrhGV/IMG-3881.png" width="300"> | *Streaming Interface* |
| <img src="https://i.postimg.cc/Yt27WBd6/IMG-3884.png" width="300"> | *Title View*        |
| <img src="https://i.postimg.cc/6tXtBvR1/IMG-3885.png" width="300"> | *Results*           |
| <img src="https://i.postimg.cc/jKNRVXW7/IMG-3883.png" width="300"> | *User Settings*     |
| <img src="https://i.postimg.cc/1yDWs8GM/IMG-3887.png" width="300"> | *Admin Settings*    |


</details>


## Features
- Account system
- Web interface for streaming with support for VLC, Infuse and VidHub
- Track users' watch history
- Fetch links from multiple addons
- Redis cache that instantly returns already fetched links
- Automatically cache all episodes in a season when any episode from that season is requested
- Optional encryption of video URLs and proxy streams to bypass IP restrictions on debrid services (at your own risk) and avoid exposing your API keys/passwords
- Optional cleansing of confusing file names, show only relevant metadata
- Optional filtering of duplicate streams, show only the best file available per resolution
- Very easy to add support for new addons

## Supported Stremio Addons
- [Torrentio](https://torrentio.strem.fun/)
- [Comet](https://comet.elfhosted.com/)
- [MediaFusion](https://mediafusion.elfhosted.com/)
- [TorBox](https://torbox.app/)
- [Easynews](https://ea627ddf0ee7-easynews.baby-beamup.club/)
- [Debridio](https://debridio.adobotec.com/)
- [WatchHub](https://watchhub.stkc.win/)
- [Peerflix](https://config.peerflix.mov/)

## Supported Debrid Providers
All debrid providers supported in the addons listed above

> [!WARNING]
> If your debrid provider has IP sharing restrictions, and you will be accessing this addon from multiple IPs, you must configure the proxy to be ON for ALL users. If you will only be accessing this addon from one network it is safe to disable the proxy.
>
> Services such as TorBox and Premiumize do not have this restriction and you are free to enable the proxy for some users and disable it for others.

## Setup
<details>
<summary>Setup Guide</summary>

Requirements:

- Docker
- Reverse proxy (https://caddyserver.com/docs/quick-starts/reverse-proxy)

1. Clone the repo: `git clone https://github.com/stekc/AIOStremio`
2. Copy and rename .env.example to .env and fill out the required fields:

Create an admin account that will be used to add new users and toggle proxy streams:
```
ADMIN_USERNAME=
ADMIN_PASSWORD=
```
If you are using MediaFlow, or not using the proxy at all, this can be left blank. If using the built-in proxy, run `python3 gen_key.py` and add the key:
```
ENCRYPTION_KEY=
```
If you are proxying streams with MediaFlow, generate a secure password to prevent unauthorized access:
```
MEDIAFLOW_API_KEY=
```
When set to true, MediaFlow will log detailed proxied stream info:
```
MEDIAFLOW_STREAMING_PROGRESS=true
```
Your Real-Debrid/Premiumize/TorBox/etc. API key. If you are only using EasyNews, this can be left blank:
```
DEBRID_API_KEY=
```
Generate a MediaFusion manifest at https://mediafusion.elfhosted.com/, then copy the string of random characters between `https://mediafusion.elfhosted.com/` and `/manifest.json`. If you do not want to use MediaFusion, leave this field blank:
```
MEDIAFUSION_OPTIONS=
```
Your EasyNews username and password. If you are only using a debrid service, this can be left blank:
```
EASYNEWS_USERNAME=
EASYNEWS_PASSWORD=
```
Generate a secure password for the Redis cache. Host and port should be left as default when using Docker:
```
REDIS_HOST=debridproxy_redis
REDIS_PORT=6379
REDIS_PASSWORD=
```

3. Copy and rename config.json.example to config.json and fill out the required fields:

If using a debrid service, specify it here:
```
"debrid_service": "torbox",
```
If you want to use different debrid services for different addons, specify them here, otherwise leave blank:
```
"addon_config": {
    "torrentio": {
        "debrid_service": "",
        "debrid_api_key": ""
    },
    "comet": {
        "base_url": "https://comet.elfhosted.com",
        "debrid_service": "",
        "debrid_api_key": ""
    },
    "debridio": {
        "debrid_service": "easydebrid",
        "debrid_api_key": ""
    },
    "peerflix": {
        "debrid_service": "",
        "debrid_api_key": ""
    }
},
```
The domain where the addon will be accessible:
```
"addon_url": "https://debridproxy.your-domain.com",
```
The domain used when generating links, leave as default unless using another instance (ElfHosted, etc.):
```
"mediaflow_url": "http://debridproxy_mediaflow:8888",
```
The domain returned in the generated links, set this to your domain:
```
"external_mediaflow_url": "https://mediaflow.your-domain.com",
```
When disabled, the addon will use the built-in proxy streaming. Unless you experience issues with MediaFlow, leave this set to true:
```
"mediaflow_enabled": true,
```
How long in seconds fetched links will be cached:
```
"cache_ttl_seconds": 604800,
```
Advanced built-in proxy options. Does not affect MediaFlow. Leave this as default unless the built-in proxy has issues:
```
"buffer_size_mb": 256,
"chunk_size_mb": 4,
```

3. Configure your reverse proxy. If you are using Caddy in Docker, this Caddyfile should work:
```
aiostremio.your-domain.com {
    reverse_proxy debridproxy:8469
}
 
mediaflow.your-domain.com {
    reverse_proxy debridproxy_mediaflow:8888
}
```

4. Run `docker compose up -d` to start the addon.

5. Navigate to aiostremio.your-domain.com/admin to add a user

6. Navigate to aiostremio.your-domain.com/ to generate a manifest

7. Add the generated URL to Stremio/Vidi/etc. and start watching
</details>

## Credits
Torrentio, Comet, MediaFusion, and all other upstream addons - Used for fetching links

[MediaFlow](https://github.com/mhdzumair/mediaflow-proxy) - Used for proxy streams

## Notes
- MediaFlow is recommended for video proxying, though you can use the internal proxy by editing the config if you have issues
- AIOStremio is primarily tested with TorBox. Please open an issue if other debrid services do not work
- Bypassing IP restrictions on debrid services is experimental

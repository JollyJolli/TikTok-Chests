from app.discovery.base import DiscoveryProvider, DiscoveryResult


class ManualOnlyProvider(DiscoveryProvider):
    name = "manual"

    async def discover(self) -> DiscoveryResult:
        return DiscoveryResult(
            available=False,
            message=(
                "TikTok's public LIVE directory is browser-rendered, but no stable "
                "credential-free server feed is enabled. Add public usernames or LIVE URLs manually."
            ),
        )

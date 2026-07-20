from abc import ABC, abstractmethod
from typing import List
from aegisScout.discovery.models import LeadCandidate

class BaseDiscoveryProvider(ABC):
    @abstractmethod
    async def search(
        self, sector: str, location: str, radius_km: int = 10
    ) -> List[LeadCandidate]:
        """
        Search for businesses based on sector, location, and radius.
        """
        pass

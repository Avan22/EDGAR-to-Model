import httpx
from aiolimiter import AsyncLimiter
from tenacity import retry, stop_after_attempt, wait_exponential
from .settings import settings

class SecClient:
    def __init__(self):
        self._limiter = AsyncLimiter(max_rate=settings.sec_rps, time_period=1.0)
        self._client = httpx.AsyncClient(
            timeout=httpx.Timeout(30.0),
            headers={
                "User-Agent": settings.sec_user_agent,
                "Accept-Encoding": "gzip, deflate, br",
                "Accept": "application/json",
            },
        )

    async def aclose(self):
        await self._client.aclose()

    @retry(stop=stop_after_attempt(5), wait=wait_exponential(multiplier=0.6, min=0.6, max=8))
    async def get_json(self, url: str):
        async with self._limiter:
            r = await self._client.get(url)
        r.raise_for_status()
        return r.json()

    async def tickers(self):
        return await self.get_json("https://www.sec.gov/files/company_tickers.json")

    async def companyfacts(self, cik: int):
        cik10 = str(cik).zfill(10)
        return await self.get_json(f"https://data.sec.gov/api/xbrl/companyfacts/CIK{cik10}.json")

    async def submissions(self, cik: int):
        cik10 = str(cik).zfill(10)
        return await self.get_json(f"https://data.sec.gov/submissions/CIK{cik10}.json")

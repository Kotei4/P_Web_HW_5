import aiohttp
import asyncio
from datetime import datetime, timedelta
import json
import aiofile
from aiopath import AsyncPath

class CurrencyFetcher:
    def __init__(self, days, currencies):
        self.days = min(max(1, days), 10)
        self.currencies = currencies
        self.url = "https://api.privatbank.ua/p24api/exchange_rates?json&date="

    async def fetch(self, session, date):
        async with session.get(self.url + date.strftime("%d.%m.%Y")) as response:
            return await response.text()

    async def get_currency_rates(self):
        async with aiohttp.ClientSession() as session:
            tasks = []
            for i in range(self.days):
                date = datetime.now() - timedelta(days=i)
                tasks.append(self.fetch(session, date))
            responses = await asyncio.gather(*tasks)
            return responses

    def parse_responses(self, responses):
        result = []
        for response in responses:
            data = json.loads(response)
            if 'exchangeRate' in data:
                rates = {x['currency']: {'sale': x['saleRateNB'], 'purchase': x['purchaseRateNB']} for x in data['exchangeRate'] if x['currency'] in self.currencies}
                if rates:
                    result.append({data['date']: rates})
        return result

    async def run(self):
        responses = await self.get_currency_rates()
        result = self.parse_responses(responses)
        async with aiofile.AIOFile('exchange.log', 'w') as afp:
            writer = aiofile.Writer(afp)
            await writer(f"Exchange command executed at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            await writer(json.dumps(result, indent=2, ensure_ascii=False))
        return result

if __name__ == "__main__":
    fetcher = CurrencyFetcher(10, ['EUR', 'CHF', 'PLN', 'USD'])
    rates = asyncio.run(fetcher.run())
    print(json.dumps(rates, indent=2, ensure_ascii=False))
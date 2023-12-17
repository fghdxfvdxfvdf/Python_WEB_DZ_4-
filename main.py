import asyncio
import json
import logging
import platform
import sys
from datetime import date, datetime, timedelta

import aiohttp
from aiofile import async_open

API_WHITHOUT_DATA = "https://api.privatbank.ua/p24api/exchange_rates?date="
DAY_NUMBER = int(sys.argv[1])


async def date_days(days: int) -> list:
    if days < 1 or days > 10:
        raise ValueError("The number %s of days must be between 1 and 10", days)

    date_now = date.today()
    date_list = []
    try:
        for day in range(days):
            data = date_now - timedelta(days=day)
            data = datetime(year=data.year, month=data.month, day=data.day)
            date_list.append(data.strftime("%d.%m.%Y"))
        return date_list
    except TypeError as e:
        raise ValueError(f'Error: {e}, days must be an integer from 1 to 10') from e



async def api_days_list() -> list:
    res_list = []
    for date_item in await date_days(DAY_NUMBER):
        res_list.append(API_WHITHOUT_DATA + date_item)
    return res_list


async def request() -> list:
    async with aiohttp.ClientSession() as session:
        res_list = []
        for api in await api_days_list():
            logging.info(f"Starting {api}")

            try:
                async with session.get(api) as response:
                    if response.status == 200:
                        res = await response.json()
                        res_list.append(res)

                    else:
                        logging.error(f"Error status {response.status} for {api}")
                        logging.error('Error status %s for %s', response.status, api)

            except aiohttp.ClientConnectionError as e:
                logging.exception(f"Connect {api}: {e}")

        return res_list


async def form():
    tasks = [request(), api_days_list()]
    dict_data_list, dates_list = await asyncio.gather(*tasks)

    res_list = []
    for dict_data in dict_data_list:
        new_dict = {}
        for iter in dict_data["exchangeRate"]:
            if iter["currency"] == "EUR":
                new_dict.update(
                    {
                        "EUR": {
                            "sale": iter["saleRateNB"],
                            "purchase": iter["purchaseRateNB"],
                        }
                    }
                )
            elif iter["currency"] == "USD":
                new_dict.update(
                    {
                        "USD": {
                            "sale": iter["saleRateNB"],
                            "purchase": iter["purchaseRateNB"],
                        }
                    }
                )

        res_list.append({dict_data["date"]: new_dict})

    # Write the entire list as a JSON array to the file text_file.json
    async with async_open("text_file.json", "w") as afp:
        await afp.write(json.dumps(res_list, indent=2))

    return res_list


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG, format="%(message)s")

    if platform.system() == "Windows":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

    r = asyncio.run(form())
    print(r)

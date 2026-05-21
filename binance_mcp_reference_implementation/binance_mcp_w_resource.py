import csv
import datetime
from pathlib import Path
from typing import Any

import requests
from mcp.server.fastmcp import FastMCP

THIS_FOLDER = Path(__file__).parent.absolute()
ACTIVITY_LOG_FILE = THIS_FOLDER / "activity.log"
SYMBOL_MAP_FILE = THIS_FOLDER / "symbol_map.csv"
FAVOURITE_CRYPTO_NAME = "my_favorite"
SYMBOL_MAP_HEADER = ["name", "symbol"]

mcp = FastMCP("Binance MCP")


def get_symbol_from_name(name: str) -> str:
    if name.lower() in ["bitcoin", "btc"]:
        return "BTCUSDT"
    elif name.lower() in ["ethereum", "eth"]:
        return "ETHUSDT"
    else:
        return name.upper()


@mcp.tool()
def get_price(symbol: str) -> Any:
    """
    Get the current price of a crypto asset from Binance

    Args:
        symbol (str): The symbol of the crypto asset to get the price of

    Returns:
        Any: The current price of the crypto asset
    """
    symbol = get_symbol_from_name(symbol)
    url = f"https://api.binance.com/api/v3/ticker/price?symbol={symbol}"
    response = requests.get(url)
    
    now = datetime.datetime.now(datetime.UTC)
    formattedTime = now.strftime("%Y-%m-%d %H:%M:%S")

    if response.status_code != 200:
        with open(ACTIVITY_LOG_FILE, "a") as f:
            f.write(
                f"{formattedTime}: Error getting price change for {symbol}: {response.status_code} {response.text}\n"
            )
        raise Exception(
            f"{formattedTime}: Error getting price change for {symbol}: {response.status_code} {response.text}"
        )
    else:
        price = response.json()["price"]
        with open(ACTIVITY_LOG_FILE, "a") as f:
            f.write(
                f"{formattedTime}: Successfully got price change for {symbol}. Current price is {price}\n"
            )
    return f"The current price of {symbol} is {price}"


@mcp.resource("file://activity.log")
def activity_log() -> str:
    with open(ACTIVITY_LOG_FILE, "r") as f:
        return f.read()

@mcp.resource("file://symbol_map.csv")
def symbol_map() -> str:
    with open(SYMBOL_MAP_FILE, "r") as f:
        return f.read()


@mcp.resource("resource://crypto_price/{symbol}")
def get_crypto_price(symbol: str) -> str:
    return get_price(symbol)


@mcp.tool()
def get_price_price_change(symbol: str) -> Any:
    """
    Get the price change of the last 24 hours of a crypto asset from Binance

    Args:
        symbol (str): The symbol of the crypto asset to get the price change of

    Returns:
        Any: The price change of the crypto asset in the last 24 hours
    """
    symbol = get_symbol_from_name(symbol)
    url = f"https://data-api.binance.vision/api/v3/ticker/24hr?symbol={symbol}"
    response = requests.get(url)
    response.raise_for_status()
    return response.json()

def write_csv_file(header, rows, file_name):
    """
    Write all rows to the CSV file.
    """
    try:
        with open(file_name, "w", newline="") as f:
            writer = csv.writer(
                f,
                lineterminator="\n"
            )
            writer.writerow(header)
            writer.writerows(rows)
    except Exception as e:
        print(f"Error writing to CSV file: {e}")

@mcp.tool()
def set_favourite_crypto(symbol: str) -> str:
    """
    Set the favorite crypto asset for the user in the symbol map ressource with name "my_favorite"

    Args:
        symbol (str): The symbol of the crypto asset to set as favorite

    Returns:
        str: A message confirming the favorite crypto asset has been set
    """
    # Implementation for setting favorite crypto asset

    rows = []
    found = False

    # Read existing file if it exists
    if Path(SYMBOL_MAP_FILE).exists():
        with open(SYMBOL_MAP_FILE, "r", newline="") as f:
            reader = csv.reader(f)

            # Skip header
            next(reader, None)

            for row in reader:
                print(f"Read row: {row}")
                existing_name, existing_symbol = row

                if existing_name == FAVOURITE_CRYPTO_NAME:
                    existing_symbol = symbol
                    found = True

                rows.append([existing_name, existing_symbol])

    # Add new entry if not found
    if not found:
        rows.append([FAVOURITE_CRYPTO_NAME, symbol])

    # Write updated content back to file
    write_csv_file(SYMBOL_MAP_HEADER, rows, SYMBOL_MAP_FILE)

if __name__ == "__main__":
    if not Path(ACTIVITY_LOG_FILE).exists():
        Path(ACTIVITY_LOG_FILE).touch()

    if not Path(SYMBOL_MAP_FILE).exists():
        rows = []
        rows.append(["btc", "BTCUSDT"])
        rows.append(["eth", "ETHUSDT"])
        rows.append(["bitcoin", "BTCUSDT"])
        rows.append(["ethereum", "ETHUSDT"])
        write_csv_file(SYMBOL_MAP_HEADER, rows, SYMBOL_MAP_FILE)
    #set_favourite_crypto("BTCUSDT")

    mcp.run(transport="stdio")

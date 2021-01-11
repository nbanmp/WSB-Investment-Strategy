#!/usr/bin/env python3
"Gets WSB's Best Stock"
from datetime import datetime
import time
import json
import logging
import os
import requests
import sys
import tempfile

tmpfile = tempfile.mktemp()

if "--debug" in sys.argv:
    logging.basicConfig(level=logging.DEBUG)

logging.getLogger("urllib3").setLevel(logging.WARNING)
log = logging.getLogger(__name__)


def add_text(text):
    # We don't like ETFs and random abbreviations. The goal is to find the best stock.
    ignore_list = [
        "SPAC",
        "US",
        "DD",
        "WSB",
        "CEO",
        "PM",
        "OP",
        "ETF",
        "THIS",
        "IV",
        "THE",
        "EOD",
        "RH",
        "SPY",
        "FD",
        "NSE",
        "SP",
        "SPX",
        "VIX",
        "VXX",
        "OTM",
        "ITM",
        "FOMO",
        "ER",
        "IPO",
        "TLDR",
        "DIX",
        "RIP",
        "LOL",
    ]

    capitals = "".join([c for c in text if c.isupper() or c.isspace()])
    # Remove set() if looking for total number of uses, not number per post/comment.
    capitals = "\n".join(
        [s for s in set(capitals.split()) if len(s) >= 2 and s not in ignore_list]
    )
    if capitals:
        with open(tmpfile, "a") as f:
            f.write(capitals + "\n")


def get_stock():
    "Gets WSB's Best Stock"

    log.debug("Using temporary file {}.".format(tmpfile))

    with open(tmpfile, "w") as f:
        f.write("")

    if "--date" in sys.argv:
        try:
            date = sys.argv[sys.argv.index("--date") + 1]
            end_time = int(datetime.strptime(date, "%Y-%m-%d").timestamp())
        except (IndexError, ValueError):
            print("Usage: {} --date YYYY-MM-DD".format(sys.argv[0]))
            sys.exit()
    else:
        end_time = int(time.time())

    start_time = end_time - 24 * 60 * 60
    # two_days_ago_time = day_ago_time - 24 * 60 * 60

    r = requests.get(
        "https://api.pushshift.io/reddit/submission/search",
        params={
            "subreddit": "wallstreetbets",
            "sort_type": "num_comments",  # "num_comments"
            "sort": "desc",
            "size": 20,  # Number of results to return <= 500
            "before": end_time,
            "after": start_time,
        },
    )

    posts = json.loads(r.text)["data"]
    log.debug("Got {} posts.".format(len(posts)))

    for post in posts:
        log.debug(
            "Adding post https://reddit.com{} with {} comments.".format(
                post["permalink"], post["num_comments"]
            )
        )

        add_text(post["selftext"])

        r = requests.get(
            "https://api.pushshift.io/reddit/comment/search",
            params={
                "link_id": post["id"],
                "limit": 20000,
                "sort": "desc",
                "sort_type": "score",
            },
        )

        comments = json.loads(r.text)["data"]
        log.debug("Got {} comments from post.".format(len(comments)))
        for comment in comments:
            add_text(comment["body"])

    with open(tmpfile, "r") as f:
        stocks = f.read().split()

    os.remove(tmpfile)
    log.debug("Removed temporary file {}".format(tmpfile))

    stock_counts = {}
    for stock in stocks:
        try:
            stock_counts[stock] += 1
        except KeyError:
            stock_counts[stock] = 1

    stock_order = list(stock_counts.keys())
    stock_order.sort(key=stock_counts.get, reverse=True)

    log.info("Top 10:")
    for stock in stock_order[:10]:
        log.info("{}: {}".format(stock, stock_counts[stock]))

    return stock_order[0]


if __name__ == "__main__":
    print("Downloading top stocks from the best sources...")
    print("Please wait a few moments as we crunch the numbers.")
    print("")
    print("Buy {}.".format(get_stock()))

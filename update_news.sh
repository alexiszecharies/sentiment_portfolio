#!/bin/bash
cd /home/azecharies/yahoo_news_sentiment
git pull
python3 scrape_yahoo_news.py
git add .
git commit -m "update news"
git push

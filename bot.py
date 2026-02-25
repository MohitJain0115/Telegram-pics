import feedparser
import requests
import os
import random
import re

# ========= CONFIG =========

RSS_FEEDS = [
    "https://in.pinterest.com/kalpanamehra5656/desi-girls.rss",
    "https://in.pinterest.com/kalpanamehra5656/actresses.rss",
    "https://in.pinterest.com/iamtheavijeet/beauty-girl.rss"
]
import os
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = "@indianhotpics"

# ===========================


# ---------- STORAGE ----------

def load_posted_links():
    if not os.path.exists("posted_links.txt"):
        return set()

    with open("posted_links.txt", "r") as f:
        return set(line.strip() for line in f.readlines())


def save_posted_link(link):
    with open("posted_links.txt", "a") as f:
        f.write(link + "\n")


# ---------- IMAGE EXTRACTION ----------

def extract_image(entry):
    if "summary" in entry:
        match = re.search(r'<img.*?src="(.*?)"', entry.summary)
        if match:
            return match.group(1)
    return None


def get_random_pin_from_feed(feed_url, posted_links):
    feed = feedparser.parse(feed_url)

    if not feed.entries:
        return None

    unposted = [e for e in feed.entries if e.link not in posted_links]

    if not unposted:
        return None

    selected = random.choice(unposted)

    image_url = extract_image(selected)
    caption = selected.title
    link = selected.link

    return image_url, caption, link


def get_random_pin_from_multiple_feeds():
    posted_links = load_posted_links()

    feeds = RSS_FEEDS.copy()
    random.shuffle(feeds)  # randomize feed order

    for feed_url in feeds:
        result = get_random_pin_from_feed(feed_url, posted_links)

        if result:
            print(f"Selected from feed: {feed_url}")
            return result

    return None


# ---------- TELEGRAM ----------

def send_to_telegram(image_url, caption):
    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.get(image_url, headers=headers)

        if response.status_code != 200:
            return None

        with open("temp.jpg", "wb") as f:
            f.write(response.content)

        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendPhoto"

        with open("temp.jpg", "rb") as img:
            telegram_response = requests.post(
                url,
                data={
                    "chat_id": CHAT_ID,
                    "caption": f"{caption}\n\n🔥 Vote below 👇"
                },
                files={"photo": img}
            )

        os.remove("temp.jpg")
        return telegram_response.json()

    except Exception as e:
        print("Error sending image:", e)
        return None


def get_random_question():
    questions = [
        ("Would you take her on a date? 😉", '["Absolutely 😍","Maybe 😏"]'),
        ("How hot is this look? 🔥", '["10/10 🥵","Pretty good 😎","Not my type"]'),
        ("Be honest… would you stare? 👀", '["Couldn’t stop 😍","Just a little 😉"]'),
        ("Is she your type? 😉", '["100% 😍","Not really 🤷‍♂️"]')
    ]

    return random.choice(questions)


def send_poll(question, options):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendPoll"

    payload = {
        "chat_id": CHAT_ID,
        "question": question,
        "options": options,
        "is_anonymous": True
    }

    response = requests.post(url, data=payload)
    return response.json()


# ---------- MAIN ----------

if __name__ == "__main__":
    data = get_random_pin_from_multiple_feeds()

    if data:
        image_url, caption, link = data

        result = send_to_telegram(image_url, caption)
        print(result)

        if result and result.get("ok"):
            save_posted_link(link)

            question, options = get_random_question()
            poll_result = send_poll(question, options)
            print(poll_result)

    else:
        print("All feeds exhausted.")
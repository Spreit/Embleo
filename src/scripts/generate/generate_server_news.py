"""Generate an optional setup notice without changing upstream announcements."""
import datetime
import html
import json
import os
from pathlib import Path

NEWS_ID = "server-setup"
DEFAULT_TITLE = "Embleo Server"
DEFAULT_CONTENT = "Welcome to Tales of Luminaria."


def news_settings_from_environment():
    return {
        "enabled": os.getenv("EMBLEO_NEWS_ENABLED", "1").lower() not in ("0", "false", "no"),
        "title": os.getenv("EMBLEO_NEWS_TITLE", DEFAULT_TITLE),
        "content": os.getenv("EMBLEO_NEWS_CONTENT", DEFAULT_CONTENT),
    }


def ask_news_settings():
    settings = news_settings_from_environment()
    default = "Y/n" if settings["enabled"] else "y/N"
    answer = input("Add a server welcome notice? [{0}]: ".format(default)).strip().lower()
    if answer:
        settings["enabled"] = answer in ("y", "yes")
    if settings["enabled"]:
        settings["title"] = input("News title [{0}]: ".format(settings["title"])).strip() or settings["title"]
        settings["content"] = input("News content [{0}]: ".format(settings["content"])).strip() or settings["content"]
    return settings


def generate_server_news(settings=None, path="./offline_responses/api/news/list.json", now=None):
    settings = news_settings_from_environment() if settings is None else settings
    if not settings.get("enabled", True):
        return
    path = Path(path)
    data = json.loads(path.read_text(encoding="utf-8"))
    existing = [entry for entry in data["News"] if entry["NewsId"] == NEWS_ID]
    templates = existing or data["News"]
    # Copy an existing definition so the client receives no additional fields.
    notice = dict(templates[0]) if templates else {
        "NewsId": NEWS_ID, "Title": DEFAULT_TITLE, "Content": DEFAULT_CONTENT,
        "StartAt": 1658250000, "EndAt": 1784480400, "IsNew": False, "Status": 1,
    }
    date = now or datetime.datetime.now(datetime.timezone.utc)
    if date.tzinfo is None:
        date = date.replace(tzinfo=datetime.timezone.utc)
    duration = notice["EndAt"] - notice["StartAt"]
    notice["NewsId"] = NEWS_ID
    notice["Title"] = settings.get("title") or DEFAULT_TITLE
    content = settings.get("content") or DEFAULT_CONTENT
    # Treat operator input as text; only line breaks become known HTML markup.
    notice["Content"] = "<br>".join(html.escape(line) for line in content.splitlines())
    notice["StartAt"] = int(date.timestamp())
    notice["EndAt"] = notice["StartAt"] + duration
    data["News"] = [notice] + [entry for entry in data["News"] if entry["NewsId"] != NEWS_ID]
    temporary = path.with_name(path.name + ".pending")
    temporary.write_text(json.dumps(data, ensure_ascii=False, indent=4) + "\n", encoding="utf-8")
    temporary.replace(path)

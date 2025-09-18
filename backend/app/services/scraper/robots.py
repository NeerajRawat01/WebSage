from urllib.parse import urlparse, urlunparse
import urllib.robotparser as robotparser


def robots_txt_url(target_url: str) -> str:
    parsed = urlparse(target_url)
    robots = parsed._replace(path="/robots.txt", params="", query="", fragment="")
    return urlunparse(robots)


def can_fetch(user_agent: str, target_url: str) -> bool:
    rp = robotparser.RobotFileParser()
    rp.set_url(robots_txt_url(target_url))
    try:
        rp.read()
    except Exception:
        # If robots can't be read, default to allowing (fail-open) per plan can be tuned
        return True
    return rp.can_fetch(user_agent, target_url)



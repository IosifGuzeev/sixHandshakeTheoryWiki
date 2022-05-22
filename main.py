from bs4 import BeautifulSoup
from ratelimiter import RateLimiter

import requests
import sys

USED_LINKS = set()
PATH_RESULT = None


def get_content(link):
    response = requests.get(link)
    if response.reason != "OK":
        raise Exception(f"Cant get content from link {link}\n Request data: {response.data}")
    return requests.get(link).content


def get_list_of_links(content):
    soup = BeautifulSoup(content, 'html.parser')

    # Non-English article
    if soup.html["lang"] != 'en':
        return []
    return soup.find(id="bodyContent").find_all("a", href=True)


def is_internal_link(link):
    return "/wiki/" in link


def is_article_link(link, sort_lists=False, sort_indexes=False):
    # "Category:" "File:"
    is_article = ":" not in link
    if sort_lists:
        is_article = is_article and "List" not in link
    if sort_indexes:
        is_article = is_article and "Index" not in link

    return is_article


def get_article_links(links):
    return [link['href'] for link in links if is_internal_link(link['href']) and is_article_link(link['href'])]


def get_full_wiki_link(link):
    base = "https://en.wikipedia.org"
    return base + link


def get_link_path(current_link, destination, get_content_function, current_depth=0, max_depth=6, path=None):
    global PATH_RESULT, USED_LINKS

    # print(current_link, destination)
    if current_link == destination:
        PATH_RESULT = path
        return None
    if (current_depth == max_depth) or (PATH_RESULT is not None):
        return None
    USED_LINKS.add(current_link)

    if path is None:
        path = []
    print(f"Link: {current_link} depth: {len(path)}")

    content = get_content_function(current_link)
    links = get_list_of_links(content)
    links = get_article_links(links)
    links = [get_full_wiki_link(link) for link in links]
    if destination in set(links):
        PATH_RESULT = path
        return None
    result = [
        get_link_path(
            link,
            destination,
            get_content_function,
            current_depth + 1,
            max_depth=max_depth,
            path=path + [current_link],
        ) for link in links if link not in USED_LINKS
    ]
    for res in result:
        if res is not None:
            PATH_RESULT = res
            break


if __name__ == '__main__':
    # Examples
    # 1 node:
    # https://en.wikipedia.org/wiki/Six_degrees_of_separation https://en.wikipedia.org/wiki/American_Broadcasting_Company 10
    # 5 nodes
    # https://en.wikipedia.org/wiki/Six_degrees_of_separation https://en.wikipedia.org/wiki/Short_film 10
    link_a, link_b, rate_limit = sys.argv[1:4]
    print("Start: ", link_a)
    print("Destination: ", link_b)
    print("Rate limit: ",  rate_limit)

    get_content_function = RateLimiter(max_calls=int(rate_limit), period=60)(get_content)
    get_link_path(link_a, link_b, get_content_function)
    if PATH_RESULT is None:
        print("Path is not found!")
    else:
        print(link_a, " => ", " => ".join(PATH_RESULT[1:]), " => ", link_b)

import sys

content = """
async def fetch_official_company_news() -> List[Dict[str, Any]]:
    \"\"\"
    Fetch official news from Nvidia, OpenAI, and Microsoft.
    Returns approximately 12-15 articles total.
    \"\"\"
    logger.info("Fetching official company news...")
    articles = []
    
    # Official feeds
    feeds = [
        {"name": "Nvidia", "url": "https://nvidianews.nvidia.com/releases.xml"},
        {"name": "Microsoft", "url": "https://news.microsoft.com/feed/"},
        {"name": "OpenAI", "url": "https://openai.com/news/rss.xml"}
    ]
    
    async def fetch_feed(feed: Dict[str, str], client: httpx.AsyncClient) -> Optional[str]:
        try:
            logger.info(f"Fetching Official RSS feed: {feed['name']} ({feed['url']})")
            response = await client.get(feed["url"], timeout=10.0)
            if response.status_code == 200:
                return response.text
        except Exception as e:
            logger.warning(f"Failed to fetch Official RSS feed {feed['name']}: {e}")
        return None

    timeout_cfg = httpx.Timeout(connect=3.0, read=10.0, write=3.0, pool=5.0)
    async with httpx.AsyncClient(timeout=timeout_cfg, follow_redirects=True) as client:
        tasks = [fetch_feed(feed, client) for feed in feeds]
        xml_contents = await asyncio.gather(*tasks)
        
    from bs4 import BeautifulSoup
    for feed, xml_content in zip(feeds, xml_contents):
        if not xml_content:
            continue
            
        try:
            soup = BeautifulSoup(xml_content, "xml")
            items = soup.find_all("item")
            is_atom = False
            if not items:
                items = soup.find_all("entry")
                is_atom = True
                
            feed_articles = []
            for item in items:
                title = ""
                url = ""
                description = ""
                pub_date = ""
                
                if is_atom:
                    title_el = item.find("title")
                    title = title_el.text if title_el else ""
                    
                    link_el = item.find("link")
                    if link_el:
                        url = link_el.get("href") or link_el.text
                        
                    summary_el = item.find("summary") or item.find("content")
                    description = summary_el.text if summary_el else ""
                    
                    pub_el = item.find("published") or item.find("updated")
                    pub_date = pub_el.text if pub_el else ""
                else:
                    title_el = item.find("title")
                    title = title_el.text if title_el else ""
                    
                    link_el = item.find("link")
                    url = link_el.text if link_el else ""
                    
                    desc_el = item.find("description")
                    description = desc_el.text if desc_el else ""
                    
                    pub_el = item.find("pubDate")
                    pub_date = pub_el.text if pub_el else ""
                    
                title = title.strip()
                url = url.strip()
                description = description.strip()
                pub_date = pub_date.strip()
                
                if not title or not url:
                    continue
                    
                feed_articles.append({
                    "title": title,
                    "url": url,
                    "source": feed["name"],
                    "published_at": pub_date,
                    "description": description[:300]
                })
                
            # Take top 5 from this feed
            articles.extend(feed_articles[:5])
        except Exception as e:
            logger.warning(f"Error parsing XML content for Official RSS feed '{feed['name']}': {e}")
            
    # Fallback/Scraping for OpenAI if RSS is empty or fails
    has_openai = any(a["source"] == "OpenAI" for a in articles)
    if not has_openai:
        logger.info("OpenAI RSS missing, attempting direct scrape of openai.com/news")
        try:
            async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as client:
                response = await client.get("https://openai.com/news/")
                if response.status_code == 200:
                    soup = BeautifulSoup(response.text, "html.parser")
                    links = soup.find_all("a", href=True)
                    openai_articles = []
                    seen_urls = set()
                    for link in links:
                        href = link["href"]
                        if href.startswith("/news/") or href.startswith("https://openai.com/news/"):
                            full_url = href if href.startswith("http") else f"https://openai.com{href}"
                            if full_url not in seen_urls and len(full_url) > 25:
                                seen_urls.add(full_url)
                                text = link.text.strip()
                                if text and len(text) > 15:
                                    openai_articles.append({
                                        "title": text,
                                        "url": full_url,
                                        "source": "OpenAI",
                                        "published_at": "",
                                        "description": ""
                                    })
                    articles.extend(openai_articles[:5])
        except Exception as e:
            logger.error(f"Failed to scrape OpenAI news: {e}")
            
    logger.info(f"Fetched {len(articles)} official company articles.")
    return articles
"""

with open('backend/app/services/news_fetcher.py', 'a', encoding='utf-8') as f:
    f.write('\n' + content + '\n')

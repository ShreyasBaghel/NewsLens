import logging
import json
from typing import List, Optional
import httpx
from app.config import settings
from app.services.cache import get_cached_keywords_for_article, save_cached_keywords_for_article

logger = logging.getLogger(__name__)

async def generate_article_keywords(
    title: str,
    description: str,
    content: str,
    url: str,
    client: Optional[httpx.AsyncClient] = None
) -> List[str]:
    """
    Generates exactly 3 semantic search keywords for an article using Gemini.
    Uses cached keywords if already generated and valid.
    """
    # 1. Check cache first
    cached_kws = get_cached_keywords_for_article(url)
    if cached_kws:
        logger.info(f"Using cached keywords for article: {url} -> {cached_kws}")
        return cached_kws

    forbidden = {"news", "article", "update", "latest", "report", "today", "technology", "business", "company", "information"}

    # If mock article or empty content, return empty list (no keywords)
    if "-mock.com" in url or not content:
        logger.info(f"Skipping keyword generation for mock/empty-content article: {url}")
        return []

    import time
    ollama_endpoint = f"{settings.ollama_url_resolved}/api/generate"
    
    system_prompt = (
        "You are an expert news analyst. Analyze the provided article's title, summary, and content to identify exactly 3 concise, high-quality, meaningful semantic search keywords or tags representing the article's primary topics.\n"
        "Requirements:\n"
        "1. You MUST return exactly 3 keywords.\n"
        "2. The keywords must be unique (no duplicates).\n"
        "3. Do NOT use generic filler words like: 'news', 'article', 'update', 'latest', 'report', 'today', 'technology', 'business', 'company', 'information'.\n"
        "4. Avoid raw title word fragments unless they are meaningful proper entities (e.g. company names, products).\n"
        "5. Prefer specific topics: company names, industries, technologies, products, organizations, countries, people, events, AI topics, finance topics, scientific topics.\n"
        "Return ONLY valid JSON. No markdown. No explanations. No code fences.\n"
        "Format:\n"
        "{\n"
        '    "keywords": [\n'
        '        "...",\n'
        '        "...",\n'
        '        "..."\n'
        '    ]\n'
        "}"
    )
    
    user_prompt = f"Article Title: {title}\n"
    if description:
        user_prompt += f"Article Summary/Description: {description}\n"
    if content:
        user_prompt += f"Article Content: {content[:2000]}\n"
        
    full_prompt = f"{system_prompt}\n\n{user_prompt}"
    
    payload = {
        "model": settings.OLLAMA_MODEL,
        "prompt": full_prompt,
        "format": "json",
        "stream": False,
        "options": {
            "temperature": 0.1
        }
    }
    
    timeout_cfg = httpx.Timeout(connect=3.0, read=settings.OLLAMA_TIMEOUT or 15.0, write=3.0, pool=5.0)
    
    logger.info(
        f"Requesting Ollama keywords. URL: {url}, Title: {title}, "
        f"Model: {settings.OLLAMA_MODEL}, Endpoint: {ollama_endpoint}"
    )
    
    t_start = time.perf_counter()
    try:
        if client is not None:
            response = await client.post(ollama_endpoint, json=payload, timeout=timeout_cfg)
        else:
            async with httpx.AsyncClient(timeout=timeout_cfg) as local_client:
                response = await local_client.post(ollama_endpoint, json=payload)
                
        duration = time.perf_counter() - t_start
        logger.info(f"Ollama keyword generation request finished in {duration:.3f} seconds.")
        
        if response.status_code == 200:
            res_data = response.json()
            raw_response = res_data.get("response", "").strip()
            
            logger.info(f"Ollama keyword generation raw response text: {raw_response}")
            
            cleaned_response = raw_response
            if "```json" in cleaned_response:
                cleaned_response = cleaned_response.split("```json")[1].split("```")[0].strip()
            elif "```" in cleaned_response:
                cleaned_response = cleaned_response.split("```")[1].split("```")[0].strip()
                
            try:
                parsed = json.loads(cleaned_response)
                keywords = parsed.get("keywords", [])
                if not isinstance(keywords, list) or len(keywords) == 0:
                    raise ValueError("keywords must be a non-empty list")
            except json.JSONDecodeError as parse_err:
                logger.error(f"Ollama response parsing failed: {parse_err}. Raw response: {raw_response}")
                raise ValueError(f"Malformed JSON response from Ollama: {parse_err}")
                
            cleaned_kws = []
            seen = set()
            for k in keywords:
                k_clean = str(k).strip()
                if not k_clean:
                    continue
                k_lower = k_clean.lower()
                if k_lower in forbidden:
                    continue
                if k_lower not in seen:
                    seen.add(k_lower)
                    cleaned_kws.append(k_clean)
                    
            if len(cleaned_kws) != 3:
                if len(cleaned_kws) > 3:
                    cleaned_kws = cleaned_kws[:3]
                else:
                    fallbacks = ["Manufacturing", "Industrial Technology", "Automation", "AI", "Cement Industry"]
                    for fb in fallbacks:
                        if len(cleaned_kws) >= 3:
                            break
                        if fb.lower() not in seen and fb.lower() not in forbidden:
                            seen.add(fb.lower())
                            cleaned_kws.append(fb)
                            
            logger.info(
                f"Successfully generated and cleaned Ollama keywords. "
                f"URL: {url}, Title: {title}, Keywords: {cleaned_kws}"
            )
            save_cached_keywords_for_article(url, cleaned_kws)
            return cleaned_kws
        else:
            logger.error(f"Ollama keyword generation failed. Status code: {response.status_code}")
            raise RuntimeError(f"Ollama status code: {response.status_code}")
            
    except Exception as e:
        duration = time.perf_counter() - t_start
        logger.error(
            f"Ollama keyword generation failed after {duration:.3f}s. "
            f"Model: {settings.OLLAMA_MODEL}, URL: {url}, Title: {title}, "
            f"Exception Type: {type(e).__name__}, Exception Message: {str(e)}"
        )
        
        logger.info(
            f"No fallback keywords generated due to exception. URL: {url}, Title: {title}, "
            f"Fallback Reason: {type(e).__name__}"
        )
        return []

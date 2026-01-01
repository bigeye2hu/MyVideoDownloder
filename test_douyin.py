#!/usr/bin/env python3
"""测试抖音链接解析"""
import asyncio
import os
import httpx

async def test_parse():
    url = "https://v.douyin.com/lWTDRB54VQY"
    
    # 1. 测试解析aweme_id
    print("=== 测试解析 aweme_id ===")
    try:
        from crawlers.douyin.web.web_crawler import DouyinWebCrawler
        crawler = DouyinWebCrawler()
        aweme_id = await crawler.get_aweme_id(url)
        print(f"aweme_id: {aweme_id}")
    except Exception as e:
        print(f"解析失败: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # 2. 测试调用TikHub API
    print("\n=== 测试调用 TikHub API ===")
    api_key = os.getenv("TIKHUB_API_KEY", "")
    if not api_key:
        print("TIKHUB_API_KEY未配置")
        return
    
    base_url = os.getenv("TIKHUB_API_BASE", "https://api.tikhub.io")
    headers = {
        "Authorization": f"Bearer {api_key}",
        "accept": "application/json",
    }
    api_url = f"{base_url.rstrip('/')}/api/v1/douyin/app/v3/fetch_one_video"
    params = {"aweme_id": aweme_id}
    
    print(f"请求: {api_url}")
    print(f"参数: {params}")
    
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.get(api_url, headers=headers, params=params)
            print(f"状态码: {resp.status_code}")
            if resp.status_code == 200:
                data = resp.json()
                print(f"成功! 视频标题: {data.get('data', {}).get('aweme_detail', {}).get('desc', 'N/A')}")
            else:
                print(f"错误: {resp.text}")
    except Exception as e:
        print(f"请求失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_parse())

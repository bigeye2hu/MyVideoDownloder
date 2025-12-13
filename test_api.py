#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
抖音API测试脚本
测试我们的API节点和官方TikHub API对不同类型链接的处理能力
"""

import requests
import json
import time
from typing import Dict, Any

class DouyinAPITester:
    def __init__(self):
        # 我们的API地址
        self.our_api_base = "http://165.232.131.40:8081/api/douyin/app/v3"
        
        # 官方TikHub API地址
        self.tikhub_api_base = "https://api.tikhub.io/api/v1"
        self.tikhub_api_key = "15UHOdNA1nO0wzCjLY3PzU3dLAWLBMZc3ieJih+qbObgoVOWPiatKzmaMw=="
        
        # 测试链接
        self.test_urls = {
            "标准视频链接": "https://www.douyin.com/video/7550257032533658940",
            "短链接": "https://v.douyin.com/vsmmotm2-nw/",
            "搜索链接": "https://www.douyin.com/search/挥杆?modal_id=7527168133914037514&type=general",
            "分享文本": "8.23 复制打开抖音，看看【申东赫⛳️的作品】不懂但跟 # 高尔夫 # 高尔夫挥杆 # 高尔夫球... https://v.douyin.com/vsmmotm2-nw/ eBt:/ C@U.yt 04/06"
        }
    
    def test_our_api(self, url: str, test_name: str) -> Dict[str, Any]:
        """测试我们的API"""
        print(f"\n🔍 测试我们的API - {test_name}")
        print(f"URL: {url}")
        
        try:
            # 使用fetch_one_video_by_url端点
            response = requests.get(
                f"{self.our_api_base}/fetch_one_video_by_url",
                params={"url": url},
                timeout=30
            )
            
            result = {
                "status_code": response.status_code,
                "success": response.status_code == 200,
                "response": response.json() if response.status_code == 200 else response.text,
                "error": None
            }
            
            if response.status_code == 200:
                data = response.json()
                if data.get("code") == 200:
                    print("✅ 成功")
                    print(f"视频标题: {data.get('data', {}).get('desc', 'N/A')}")
                    print(f"作者: {data.get('data', {}).get('author', {}).get('nickname', 'N/A')}")
                else:
                    print(f"❌ API返回错误: {data.get('message', 'Unknown error')}")
            else:
                print(f"❌ HTTP错误: {response.status_code}")
                print(f"错误信息: {response.text}")
                
        except Exception as e:
            result = {
                "status_code": 0,
                "success": False,
                "response": None,
                "error": str(e)
            }
            print(f"❌ 请求异常: {e}")
        
        return result
    
    def test_tikhub_web_api(self, url: str, test_name: str) -> Dict[str, Any]:
        """测试官方TikHub Web API"""
        print(f"\n🔍 测试官方TikHub Web API - {test_name}")
        print(f"URL: {url}")
        
        try:
            headers = {
                "Authorization": f"Bearer {self.tikhub_api_key}",
                "accept": "application/json"
            }
            
            response = requests.get(
                f"{self.tikhub_api_base}/douyin/web/fetch_one_video",
                params={"url": url},
                headers=headers,
                timeout=30
            )
            
            result = {
                "status_code": response.status_code,
                "success": response.status_code == 200,
                "response": response.json() if response.status_code == 200 else response.text,
                "error": None
            }
            
            if response.status_code == 200:
                data = response.json()
                if data.get("code") == 200:
                    print("✅ 成功")
                    print(f"视频标题: {data.get('data', {}).get('desc', 'N/A')}")
                    print(f"作者: {data.get('data', {}).get('author', {}).get('nickname', 'N/A')}")
                else:
                    print(f"❌ API返回错误: {data.get('message', 'Unknown error')}")
            else:
                print(f"❌ HTTP错误: {response.status_code}")
                print(f"错误信息: {response.text}")
                
        except Exception as e:
            result = {
                "status_code": 0,
                "success": False,
                "response": None,
                "error": str(e)
            }
            print(f"❌ 请求异常: {e}")
        
        return result
    
    def test_tikhub_app_api(self, url: str, test_name: str) -> Dict[str, Any]:
        """测试官方TikHub App API"""
        print(f"\n🔍 测试官方TikHub App API - {test_name}")
        print(f"URL: {url}")
        
        try:
            headers = {
                "Authorization": f"Bearer {self.tikhub_api_key}",
                "accept": "application/json"
            }
            
            # 首先获取aweme_id
            aweme_response = requests.get(
                f"{self.tikhub_api_base}/douyin/web/get_aweme_id",
                params={"url": url},
                headers=headers,
                timeout=30
            )
            
            if aweme_response.status_code != 200:
                return {
                    "status_code": aweme_response.status_code,
                    "success": False,
                    "response": aweme_response.text,
                    "error": "Failed to get aweme_id"
                }
            
            aweme_data = aweme_response.json()
            if aweme_data.get("code") != 200:
                print(f"❌ 获取aweme_id失败: {aweme_data.get('message', 'Unknown error')}")
                return {
                    "status_code": aweme_response.status_code,
                    "success": False,
                    "response": aweme_data,
                    "error": "Failed to get aweme_id"
                }
            
            aweme_id = aweme_data.get("data")
            print(f"获取到aweme_id: {aweme_id}")
            
            # 使用aweme_id获取视频信息
            response = requests.get(
                f"{self.tikhub_api_base}/douyin/app/v3/fetch_one_video",
                params={"aweme_id": aweme_id},
                headers=headers,
                timeout=30
            )
            
            result = {
                "status_code": response.status_code,
                "success": response.status_code == 200,
                "response": response.json() if response.status_code == 200 else response.text,
                "error": None
            }
            
            if response.status_code == 200:
                data = response.json()
                if data.get("code") == 200:
                    print("✅ 成功")
                    print(f"视频标题: {data.get('data', {}).get('desc', 'N/A')}")
                    print(f"作者: {data.get('data', {}).get('author', {}).get('nickname', 'N/A')}")
                else:
                    print(f"❌ API返回错误: {data.get('message', 'Unknown error')}")
            else:
                print(f"❌ HTTP错误: {response.status_code}")
                print(f"错误信息: {response.text}")
                
        except Exception as e:
            result = {
                "status_code": 0,
                "success": False,
                "response": None,
                "error": str(e)
            }
            print(f"❌ 请求异常: {e}")
        
        return result
    
    def extract_url_from_text(self, text: str) -> str:
        """从分享文本中提取URL"""
        import re
        # 查找抖音链接
        pattern = r'https://v\.douyin\.com/[a-zA-Z0-9_-]+/'
        match = re.search(pattern, text)
        if match:
            return match.group(0)
        return ""
    
    def run_all_tests(self):
        """运行所有测试"""
        print("🚀 开始抖音API测试")
        print("=" * 60)
        
        results = {}
        
        for test_name, url in self.test_urls.items():
            print(f"\n{'='*20} {test_name} {'='*20}")
            
            # 处理分享文本，提取URL
            if test_name == "分享文本":
                extracted_url = self.extract_url_from_text(url)
                if extracted_url:
                    url = extracted_url
                    print(f"从分享文本中提取的URL: {url}")
                else:
                    print("❌ 无法从分享文本中提取有效URL")
                    continue
            
            # 测试我们的API
            our_result = self.test_our_api(url, test_name)
            
            # 等待1秒避免请求过快
            time.sleep(1)
            
            # 测试官方TikHub Web API
            tikhub_web_result = self.test_tikhub_web_api(url, test_name)
            
            # 等待1秒避免请求过快
            time.sleep(1)
            
            # 测试官方TikHub App API
            tikhub_app_result = self.test_tikhub_app_api(url, test_name)
            
            # 保存结果
            results[test_name] = {
                "url": url,
                "our_api": our_result,
                "tikhub_web": tikhub_web_result,
                "tikhub_app": tikhub_app_result
            }
            
            # 等待2秒避免请求过快
            time.sleep(2)
        
        # 生成测试报告
        self.generate_report(results)
    
    def generate_report(self, results: Dict[str, Any]):
        """生成测试报告"""
        print("\n" + "="*60)
        print("📊 测试报告")
        print("="*60)
        
        for test_name, result in results.items():
            print(f"\n🔍 {test_name}")
            print(f"测试URL: {result['url']}")
            print("-" * 40)
            
            # 我们的API
            our_success = result['our_api']['success']
            print(f"我们的API: {'✅ 成功' if our_success else '❌ 失败'}")
            
            # TikHub Web API
            tikhub_web_success = result['tikhub_web']['success']
            print(f"TikHub Web API: {'✅ 成功' if tikhub_web_success else '❌ 失败'}")
            
            # TikHub App API
            tikhub_app_success = result['tikhub_app']['success']
            print(f"TikHub App API: {'✅ 成功' if tikhub_app_success else '❌ 失败'}")
        
        # 总结
        print("\n" + "="*60)
        print("📋 总结")
        print("="*60)
        
        total_tests = len(results)
        our_success_count = sum(1 for r in results.values() if r['our_api']['success'])
        tikhub_web_success_count = sum(1 for r in results.values() if r['tikhub_web']['success'])
        tikhub_app_success_count = sum(1 for r in results.values() if r['tikhub_app']['success'])
        
        print(f"总测试数: {total_tests}")
        print(f"我们的API成功率: {our_success_count}/{total_tests} ({our_success_count/total_tests*100:.1f}%)")
        print(f"TikHub Web API成功率: {tikhub_web_success_count}/{total_tests} ({tikhub_web_success_count/total_tests*100:.1f}%)")
        print(f"TikHub App API成功率: {tikhub_app_success_count}/{total_tests} ({tikhub_app_success_count/total_tests*100:.1f}%)")
        
        # 保存详细结果到文件
        with open('test_results.json', 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        print(f"\n详细结果已保存到: test_results.json")

if __name__ == "__main__":
    tester = DouyinAPITester()
    tester.run_all_tests()


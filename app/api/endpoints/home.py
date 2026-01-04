# -*- coding: utf-8 -*-
"""
挥呗 (GreenEcho) 主页
"""
import os
from fastapi import APIRouter
from fastapi.responses import HTMLResponse

router = APIRouter()

# 获取静态文件目录
STATIC_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'web', 'static')


@router.get("/", response_class=HTMLResponse, include_in_schema=False)
async def home_page():
    """挥呗 (GreenEcho) 主页"""
    html_content = """
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>挥呗 (GreenEcho) - 一站式高尔夫学习与交流工具</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700;900&family=Noto+Sans+SC:wght@300;400;500;700&display=swap" rel="stylesheet">
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        :root {
            --primary: #00ff88;
            --primary-dark: #00cc6a;
            --accent: #00d4ff;
            --bg-dark: #0a0f1a;
            --bg-card: rgba(15, 25, 40, 0.8);
            --text: #e8f4f8;
            --text-dim: #7a8b9a;
        }
        
        body {
            font-family: 'Noto Sans SC', -apple-system, BlinkMacSystemFont, sans-serif;
            background: var(--bg-dark);
            color: var(--text);
            min-height: 100vh;
            overflow-x: hidden;
        }
        
        /* 动态背景 */
        .bg-grid {
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background-image: 
                linear-gradient(rgba(0, 255, 136, 0.03) 1px, transparent 1px),
                linear-gradient(90deg, rgba(0, 255, 136, 0.03) 1px, transparent 1px);
            background-size: 50px 50px;
            animation: gridMove 20s linear infinite;
            pointer-events: none;
            z-index: 0;
        }
        
        @keyframes gridMove {
            0% { transform: translate(0, 0); }
            100% { transform: translate(50px, 50px); }
        }
        
        .bg-glow {
            position: fixed;
            width: 600px;
            height: 600px;
            border-radius: 50%;
            filter: blur(150px);
            opacity: 0.15;
            pointer-events: none;
            z-index: 0;
        }
        
        .glow-1 {
            top: -200px;
            right: -100px;
            background: var(--primary);
            animation: float1 15s ease-in-out infinite;
        }
        
        .glow-2 {
            bottom: -200px;
            left: -100px;
            background: var(--accent);
            animation: float2 18s ease-in-out infinite;
        }
        
        @keyframes float1 {
            0%, 100% { transform: translate(0, 0) scale(1); }
            50% { transform: translate(-50px, 50px) scale(1.1); }
        }
        
        @keyframes float2 {
            0%, 100% { transform: translate(0, 0) scale(1); }
            50% { transform: translate(50px, -50px) scale(1.1); }
        }
        
        /* 导航 */
        nav {
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            z-index: 100;
            padding: 20px 50px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            background: linear-gradient(to bottom, rgba(10, 15, 26, 0.95), transparent);
        }
        
        .logo {
            font-family: 'Orbitron', monospace;
            font-size: 1.8em;
            font-weight: 900;
            letter-spacing: 2px;
            background: linear-gradient(135deg, var(--primary), var(--accent));
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            line-height: 1.2;
        }
        .logo span {
            display: block;
            font-size: 0.6em;
            letter-spacing: 1px;
            opacity: 0.8;
        }
        
        .nav-links {
            display: flex;
            gap: 30px;
        }
        
        .nav-links a {
            color: var(--text-dim);
            text-decoration: none;
            font-size: 0.9em;
            letter-spacing: 1px;
            transition: all 0.3s;
            position: relative;
        }
        
        .nav-links a:hover {
            color: var(--primary);
        }
        
        .nav-links a::after {
            content: '';
            position: absolute;
            bottom: -5px;
            left: 0;
            width: 0;
            height: 2px;
            background: var(--primary);
            transition: width 0.3s;
        }
        
        .nav-links a:hover::after {
            width: 100%;
        }
        
        /* 主区域 */
        .container {
            position: relative;
            z-index: 1;
            max-width: 1400px;
            margin: 0 auto;
            padding: 0 50px;
        }
        
        /* Hero区域 */
        .hero {
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 60px;
            padding-top: 100px;
        }
        
        .hero-content {
            flex: 1;
            max-width: 600px;
        }
        
        .hero-badge {
            display: inline-block;
            padding: 8px 20px;
            background: rgba(0, 255, 136, 0.1);
            border: 1px solid rgba(0, 255, 136, 0.3);
            border-radius: 30px;
            font-size: 0.85em;
            color: var(--primary);
            margin-bottom: 30px;
            animation: pulse 2s ease-in-out infinite;
        }
        
        @keyframes pulse {
            0%, 100% { box-shadow: 0 0 0 0 rgba(0, 255, 136, 0.4); }
            50% { box-shadow: 0 0 0 10px rgba(0, 255, 136, 0); }
        }
        
        .hero h1 {
            font-family: 'Orbitron', monospace;
            font-size: 3.5em;
            font-weight: 900;
            line-height: 1.1;
            margin-bottom: 25px;
            letter-spacing: -1px;
        }
        
        .hero h1 span {
            display: block;
            background: linear-gradient(135deg, var(--primary), var(--accent));
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
        }
        
        .hero p {
            font-size: 1.2em;
            color: var(--text-dim);
            line-height: 1.8;
            margin-bottom: 40px;
        }
        
        .cta-buttons {
            display: flex;
            gap: 20px;
            flex-wrap: wrap;
        }
        
        .btn {
            padding: 16px 36px;
            border-radius: 50px;
            font-size: 1em;
            font-weight: 600;
            text-decoration: none;
            transition: all 0.3s;
            cursor: pointer;
            border: none;
            display: inline-flex;
            align-items: center;
            gap: 10px;
        }
        
        .btn-primary {
            background: linear-gradient(135deg, var(--primary), var(--primary-dark));
            color: var(--bg-dark);
            box-shadow: 0 10px 40px rgba(0, 255, 136, 0.3);
        }
        
        .btn-primary:hover {
            transform: translateY(-3px);
            box-shadow: 0 15px 50px rgba(0, 255, 136, 0.4);
        }
        
        .btn-outline {
            background: transparent;
            color: var(--text);
            border: 2px solid rgba(255, 255, 255, 0.2);
        }
        
        .btn-outline:hover {
            border-color: var(--accent);
            color: var(--accent);
            transform: translateY(-3px);
        }
        
        /* 动画球 */
        .hero-visual {
            flex: 1;
            display: flex;
            justify-content: center;
            align-items: center;
            position: relative;
        }
        
        .golf-ball {
            width: 300px;
            height: 300px;
            border-radius: 50%;
            background: radial-gradient(circle at 30% 30%, #ffffff, #e0e0e0 40%, #b0b0b0 70%, #808080);
            box-shadow: 
                inset -30px -30px 60px rgba(0, 0, 0, 0.3),
                inset 30px 30px 60px rgba(255, 255, 255, 0.3),
                0 0 100px rgba(0, 255, 136, 0.3),
                0 0 200px rgba(0, 212, 255, 0.2);
            animation: floatBall 6s ease-in-out infinite;
            position: relative;
        }
        
        .golf-ball::before {
            content: '';
            position: absolute;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            width: 280px;
            height: 280px;
            border-radius: 50%;
            background: 
                radial-gradient(circle at 15px 15px, transparent 3px, rgba(0,0,0,0.05) 3px, rgba(0,0,0,0.05) 4px, transparent 4px);
            background-size: 20px 20px;
        }
        
        @keyframes floatBall {
            0%, 100% { transform: translateY(0) rotate(0deg); }
            50% { transform: translateY(-30px) rotate(10deg); }
        }
        
        .orbit-ring {
            position: absolute;
            border: 2px solid rgba(0, 255, 136, 0.2);
            border-radius: 50%;
            animation: rotateRing 10s linear infinite;
        }
        
        .ring-1 {
            width: 400px;
            height: 400px;
            animation-duration: 15s;
        }
        
        .ring-2 {
            width: 500px;
            height: 500px;
            animation-duration: 20s;
            animation-direction: reverse;
            border-color: rgba(0, 212, 255, 0.15);
        }
        
        @keyframes rotateRing {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
        
        .orbit-dot {
            position: absolute;
            width: 12px;
            height: 12px;
            background: var(--primary);
            border-radius: 50%;
            box-shadow: 0 0 20px var(--primary);
        }
        
        /* 功能区域 */
        .features {
            padding: 120px 0;
        }
        
        .section-header {
            text-align: center;
            margin-bottom: 80px;
        }
        
        .section-header h2 {
            font-family: 'Orbitron', monospace;
            font-size: 2.5em;
            margin-bottom: 20px;
        }
        
        .section-header p {
            color: var(--text-dim);
            font-size: 1.1em;
            max-width: 600px;
            margin: 0 auto;
        }
        
        .features-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 30px;
        }
        
        .feature-card {
            background: var(--bg-card);
            border: 1px solid rgba(255, 255, 255, 0.05);
            border-radius: 24px;
            padding: 40px;
            transition: all 0.4s;
            position: relative;
            overflow: hidden;
        }
        
        .feature-card::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            height: 3px;
            background: linear-gradient(90deg, var(--primary), var(--accent));
            transform: scaleX(0);
            transition: transform 0.4s;
        }
        
        .feature-card:hover {
            transform: translateY(-10px);
            border-color: rgba(0, 255, 136, 0.2);
            box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
        }
        
        .feature-card:hover::before {
            transform: scaleX(1);
        }
        
        .feature-icon {
            width: 70px;
            height: 70px;
            border-radius: 20px;
            background: linear-gradient(135deg, rgba(0, 255, 136, 0.1), rgba(0, 212, 255, 0.1));
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 2em;
            margin-bottom: 25px;
        }
        
        .feature-card h3 {
            font-size: 1.4em;
            margin-bottom: 15px;
            font-weight: 600;
        }
        
        .feature-card p {
            color: var(--text-dim);
            line-height: 1.7;
        }
        
        /* 统计区域 */
        .stats {
            padding: 80px 0;
            background: linear-gradient(135deg, rgba(0, 255, 136, 0.03), rgba(0, 212, 255, 0.03));
            border-top: 1px solid rgba(255, 255, 255, 0.05);
            border-bottom: 1px solid rgba(255, 255, 255, 0.05);
        }
        
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 40px;
            text-align: center;
        }
        
        .stat-item h3 {
            font-family: 'Orbitron', monospace;
            font-size: 3em;
            font-weight: 900;
            background: linear-gradient(135deg, var(--primary), var(--accent));
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            margin-bottom: 10px;
        }
        
        .stat-item p {
            color: var(--text-dim);
            font-size: 0.95em;
            letter-spacing: 1px;
        }
        
        /* 页脚 */
        footer {
            padding: 60px 0 30px;
            text-align: center;
            border-top: 1px solid rgba(255, 255, 255, 0.05);
        }
        
        .footer-logo {
            font-family: 'Orbitron', monospace;
            font-size: 1.5em;
            font-weight: 700;
            background: linear-gradient(135deg, var(--primary), var(--accent));
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            margin-bottom: 20px;
            line-height: 1.3;
        }
        .footer-logo span {
            display: block;
            font-size: 0.65em;
            letter-spacing: 1px;
            opacity: 0.8;
        }
        
        .footer-links {
            display: flex;
            justify-content: center;
            gap: 30px;
            margin-bottom: 30px;
        }
        
        .footer-links a {
            color: var(--text-dim);
            text-decoration: none;
            transition: color 0.3s;
        }
        
        .footer-links a:hover {
            color: var(--primary);
        }
        
        .copyright {
            color: var(--text-dim);
            font-size: 0.85em;
        }
        
        /* 响应式 */
        @media (max-width: 1024px) {
            nav {
                padding: 15px 30px;
            }
            
            .container {
                padding: 0 30px;
            }
            
            .hero {
                flex-direction: column;
                text-align: center;
                padding-top: 120px;
            }
            
            .hero h1 {
                font-size: 2.5em;
            }
            
            .cta-buttons {
                justify-content: center;
            }
            
            .hero-visual {
                margin-top: 60px;
            }
            
            .golf-ball {
                width: 200px;
                height: 200px;
            }
            
            .ring-1 { width: 280px; height: 280px; }
            .ring-2 { width: 350px; height: 350px; }
            
            .stats-grid {
                grid-template-columns: repeat(2, 1fr);
            }
        }
        
        @media (max-width: 768px) {
            .nav-links {
                display: none;
            }
            
            .hero h1 {
                font-size: 2em;
            }
            
            .section-header h2 {
                font-size: 1.8em;
            }
            
            .stat-item h3 {
                font-size: 2em;
            }
        }
    </style>
</head>
<body>
    <!-- 背景效果 -->
    <div class="bg-grid"></div>
    <div class="bg-glow glow-1"></div>
    <div class="bg-glow glow-2"></div>
    
    <!-- 导航 -->
    <nav>
        <div class="logo">挥呗<span>GreenEcho</span></div>
        <div class="nav-links">
            <a href="#features">功能</a>
            <a href="#stats">数据</a>
            <a href="/docs">API文档</a>
        </div>
    </nav>
    
    <div class="container">
        <!-- Hero区域 -->
        <section class="hero">
            <div class="hero-content">
                <div class="hero-badge">🏌️ 一站式高尔夫学习与交流工具</div>
                <h1>
                    挥呗
                    <span>GreenEcho</span>
                </h1>
                <p>
                    支持高尔夫视频的系统化整理与回看，提供逐帧动作查看、关键动作标注工具，
                    以及击球轨迹的可视化展示。同时配备专项高尔夫 AI 助手与个人助理功能，
                    辅助您整理学习内容与练习记录。
                </p>
                <div class="cta-buttons">
                    <a href="https://apps.apple.com/app/id6504592474" class="btn btn-primary">
                        <svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor">
                            <path d="M18.71 19.5C17.88 20.74 17 21.95 15.66 21.97C14.32 22 13.89 21.18 12.37 21.18C10.84 21.18 10.37 21.95 9.1 22C7.79 22.05 6.8 20.68 5.96 19.47C4.25 16.94 2.94 12.42 4.7 9.43C5.57 7.95 7.13 7 8.82 6.97C10.1 6.94 11.32 7.83 12.11 7.83C12.89 7.83 14.37 6.76 15.92 6.93C16.57 6.96 18.39 7.18 19.56 8.9C19.47 8.96 17.09 10.35 17.12 13.22C17.16 16.71 20.13 17.82 20.17 17.84C20.14 17.91 19.68 19.39 18.71 19.5ZM13 3.5C13.73 2.67 14.94 2.04 15.94 2C16.07 3.17 15.6 4.35 14.9 5.19C14.21 6.04 13.07 6.7 11.95 6.61C11.8 5.46 12.36 4.26 13 3.5Z"/>
                        </svg>
                        App Store 下载
                    </a>
                    <a href="#features" class="btn btn-outline">了解更多</a>
                </div>
            </div>
            <div class="hero-visual">
                <div class="orbit-ring ring-1">
                    <div class="orbit-dot" style="top: -6px; left: 50%;"></div>
                </div>
                <div class="orbit-ring ring-2">
                    <div class="orbit-dot" style="bottom: -6px; right: 20%; background: var(--accent); box-shadow: 0 0 20px var(--accent);"></div>
                </div>
                <div class="golf-ball"></div>
            </div>
        </section>
        
        <!-- 功能区域 -->
        <section class="features" id="features">
            <div class="section-header">
                <h2>核心功能</h2>
                <p>一站式高尔夫学习与交流工具，为您提供专业的学习辅助功能</p>
            </div>
            <div class="features-grid">
                <div class="feature-card">
                    <div class="feature-icon">📹</div>
                    <h3>视频系统化整理</h3>
                    <p>支持高尔夫视频的系统化整理与回看，帮助您有序管理学习素材，随时回顾精彩瞬间。</p>
                </div>
                <div class="feature-card">
                    <div class="feature-icon">🎬</div>
                    <h3>逐帧动作查看</h3>
                    <p>提供逐帧动作查看功能，精确捕捉每一个动作细节，深入分析技术要领。</p>
                </div>
                <div class="feature-card">
                    <div class="feature-icon">📌</div>
                    <h3>关键动作标注</h3>
                    <p>配备关键动作标注工具，轻松标记重要时刻，快速定位学习重点。</p>
                </div>
                <div class="feature-card">
                    <div class="feature-icon">📊</div>
                    <h3>击球轨迹可视化</h3>
                    <p>提供击球轨迹的可视化展示，直观呈现球路变化，辅助技术分析。</p>
                </div>
                <div class="feature-card">
                    <div class="feature-icon">🤖</div>
                    <h3>专项高尔夫AI助手</h3>
                    <p>配备专项高尔夫 AI 助手功能，为您提供专业的建议和指导，加速学习进程。</p>
                </div>
                <div class="feature-card">
                    <div class="feature-icon">📝</div>
                    <h3>个人助理功能</h3>
                    <p>辅助您整理学习内容与练习记录，让学习更有条理，进步更有章法。</p>
                </div>
            </div>
        </section>
    </div>
    
    <!-- 统计区域 -->
    <section class="stats" id="stats">
        <div class="container">
            <div class="stats-grid">
                <div class="stat-item">
                    <h3>99.2%</h3>
                    <p>动作识别准确率</p>
                </div>
                <div class="stat-item">
                    <h3>0.1s</h3>
                    <p>分析响应时间</p>
                </div>
                <div class="stat-item">
                    <h3>30+</h3>
                    <p>关键点追踪</p>
                </div>
                <div class="stat-item">
                    <h3>24/7</h3>
                    <p>全天候服务</p>
                </div>
            </div>
        </div>
    </section>
    
    <div class="container">
        <!-- 页脚 -->
        <footer>
            <div class="footer-logo">挥呗<span>GreenEcho</span></div>
            <div class="footer-links">
                <a href="/docs">API文档</a>
                <a href="/support">技术支持</a>
                <a href="/privacy">隐私政策</a>
            </div>
            <p class="copyright">© 2026 挥呗 (GreenEcho). All rights reserved.</p>
        </footer>
    </div>
    
    <script>
        // 轨道点动画
        const dots = document.querySelectorAll('.orbit-dot');
        let angle1 = 0;
        let angle2 = Math.PI;
        
        function animateDots() {
            angle1 += 0.02;
            angle2 -= 0.015;
            
            const ring1 = document.querySelector('.ring-1');
            const ring2 = document.querySelector('.ring-2');
            
            if (dots[0] && ring1) {
                const r1 = ring1.offsetWidth / 2;
                dots[0].style.left = (r1 + r1 * Math.cos(angle1) - 6) + 'px';
                dots[0].style.top = (r1 + r1 * Math.sin(angle1) - 6) + 'px';
            }
            
            if (dots[1] && ring2) {
                const r2 = ring2.offsetWidth / 2;
                dots[1].style.left = (r2 + r2 * Math.cos(angle2) - 6) + 'px';
                dots[1].style.top = (r2 + r2 * Math.sin(angle2) - 6) + 'px';
            }
            
            requestAnimationFrame(animateDots);
        }
        
        animateDots();
        
        // 平滑滚动
        document.querySelectorAll('a[href^="#"]').forEach(anchor => {
            anchor.addEventListener('click', function (e) {
                e.preventDefault();
                const target = document.querySelector(this.getAttribute('href'));
                if (target) {
                    target.scrollIntoView({ behavior: 'smooth' });
                }
            });
        });
    </script>
</body>
</html>
"""
    return HTMLResponse(content=html_content)


@router.get("/support", response_class=HTMLResponse, include_in_schema=False)
async def support_page():
    """技术支持页面"""
    support_file = os.path.join(STATIC_DIR, 'support.html')
    if os.path.exists(support_file):
        with open(support_file, 'r', encoding='utf-8') as f:
            return HTMLResponse(content=f.read())
    return HTMLResponse(content="<h1>页面未找到</h1>", status_code=404)


@router.get("/privacy", response_class=HTMLResponse, include_in_schema=False)
async def privacy_page():
    """隐私政策页面"""
    privacy_file = os.path.join(STATIC_DIR, 'privacy.html')
    if os.path.exists(privacy_file):
        with open(privacy_file, 'r', encoding='utf-8') as f:
            return HTMLResponse(content=f.read())
    return HTMLResponse(content="<h1>页面未找到</h1>", status_code=404)


# 高尔夫视频下载 API - 使用示例

## 📱 在高尔夫 App 中集成

### 基础配置

```swift
// Swift 示例
let baseURL = "https://golf-video-api.yourdomain.com"
```

```kotlin
// Kotlin 示例
const val BASE_URL = "https://golf-video-api.yourdomain.com"
```

## 🎯 API 端点

### 1. 混合视频解析（推荐）

支持自动识别视频平台（抖音、TikTok、B站等）

**端点**: `POST /api/hybrid/video_data`

```bash
curl -X POST "https://golf-video-api.yourdomain.com/api/hybrid/video_data" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://v.douyin.com/xxx"
  }'
```

**响应示例**:
```json
{
  "code": 200,
  "message": "成功",
  "data": {
    "video_id": "7123456789",
    "title": "视频标题",
    "cover": "封面图片URL",
    "video_url": "视频下载URL",
    "music_url": "音乐下载URL",
    "author": {
      "nickname": "作者昵称",
      "avatar": "头像URL"
    },
    "statistics": {
      "play_count": 1000,
      "like_count": 100,
      "comment_count": 50
    }
  }
}
```

### 2. 抖音视频解析

**端点**: `POST /api/douyin/web/fetch_one_video`

```bash
curl -X POST "https://golf-video-api.yourdomain.com/api/douyin/web/fetch_one_video" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://v.douyin.com/xxx"
  }'
```

### 3. TikTok 视频解析

**端点**: `POST /api/tiktok/web/fetch_one_video`

```bash
curl -X POST "https://golf-video-api.yourdomain.com/api/tiktok/web/fetch_one_video" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://www.tiktok.com/@user/video/123456"
  }'
```

### 4. B站视频解析

**端点**: `POST /api/bilibili/web/fetch_one_video`

```bash
curl -X POST "https://golf-video-api.yourdomain.com/api/bilibili/web/fetch_one_video" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://www.bilibili.com/video/BVxxx"
  }'
```

## 📲 iOS App 集成示例

```swift
import Foundation

class VideoDownloadService {
    let baseURL = "https://golf-video-api.yourdomain.com"
    
    func parseVideo(url: String, completion: @escaping (Result<VideoData, Error>) -> Void) {
        let endpoint = "\(baseURL)/api/hybrid/video_data"
        
        guard let requestURL = URL(string: endpoint) else {
            completion(.failure(NSError(domain: "Invalid URL", code: -1)))
            return
        }
        
        var request = URLRequest(url: requestURL)
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        
        let body: [String: String] = ["url": url]
        request.httpBody = try? JSONEncoder().encode(body)
        
        URLSession.shared.dataTask(with: request) { data, response, error in
            if let error = error {
                completion(.failure(error))
                return
            }
            
            guard let data = data else {
                completion(.failure(NSError(domain: "No data", code: -1)))
                return
            }
            
            do {
                let result = try JSONDecoder().decode(VideoResponse.self, from: data)
                completion(.success(result.data))
            } catch {
                completion(.failure(error))
            }
        }.resume()
    }
    
    func downloadVideo(url: String, completion: @escaping (Result<URL, Error>) -> Void) {
        guard let videoURL = URL(string: url) else {
            completion(.failure(NSError(domain: "Invalid URL", code: -1)))
            return
        }
        
        let task = URLSession.shared.downloadTask(with: videoURL) { localURL, response, error in
            if let error = error {
                completion(.failure(error))
                return
            }
            
            guard let localURL = localURL else {
                completion(.failure(NSError(domain: "No file", code: -1)))
                return
            }
            
            // 移动到永久位置
            let documentsPath = FileManager.default.urls(for: .documentDirectory, in: .userDomainMask)[0]
            let destinationURL = documentsPath.appendingPathComponent("video_\(UUID().uuidString).mp4")
            
            do {
                try FileManager.default.moveItem(at: localURL, to: destinationURL)
                completion(.success(destinationURL))
            } catch {
                completion(.failure(error))
            }
        }
        
        task.resume()
    }
}

// 数据模型
struct VideoResponse: Codable {
    let code: Int
    let message: String
    let data: VideoData
}

struct VideoData: Codable {
    let videoId: String
    let title: String
    let cover: String
    let videoUrl: String
    let musicUrl: String?
    let author: Author
    let statistics: Statistics
    
    enum CodingKeys: String, CodingKey {
        case videoId = "video_id"
        case title, cover
        case videoUrl = "video_url"
        case musicUrl = "music_url"
        case author, statistics
    }
}

struct Author: Codable {
    let nickname: String
    let avatar: String
}

struct Statistics: Codable {
    let playCount: Int
    let likeCount: Int
    let commentCount: Int
    
    enum CodingKeys: String, CodingKey {
        case playCount = "play_count"
        case likeCount = "like_count"
        case commentCount = "comment_count"
    }
}
```

### 使用示例

```swift
// 解析视频
let service = VideoDownloadService()
service.parseVideo(url: "https://v.douyin.com/xxx") { result in
    switch result {
    case .success(let videoData):
        print("视频标题: \(videoData.title)")
        print("下载链接: \(videoData.videoUrl)")
        
        // 下载视频
        service.downloadVideo(url: videoData.videoUrl) { downloadResult in
            switch downloadResult {
            case .success(let fileURL):
                print("视频已保存到: \(fileURL)")
            case .failure(let error):
                print("下载失败: \(error)")
            }
        }
        
    case .failure(let error):
        print("解析失败: \(error)")
    }
}
```

## 🤖 Android App 集成示例

```kotlin
import retrofit2.Retrofit
import retrofit2.converter.gson.GsonConverterFactory
import retrofit2.http.Body
import retrofit2.http.POST
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext

// API 服务定义
interface VideoDownloadAPI {
    @POST("/api/hybrid/video_data")
    suspend fun parseVideo(@Body request: VideoRequest): VideoResponse
}

// 请求模型
data class VideoRequest(val url: String)

// 响应模型
data class VideoResponse(
    val code: Int,
    val message: String,
    val data: VideoData
)

data class VideoData(
    val video_id: String,
    val title: String,
    val cover: String,
    val video_url: String,
    val music_url: String?,
    val author: Author,
    val statistics: Statistics
)

data class Author(
    val nickname: String,
    val avatar: String
)

data class Statistics(
    val play_count: Int,
    val like_count: Int,
    val comment_count: Int
)

// 服务类
class VideoDownloadService {
    private val retrofit = Retrofit.Builder()
        .baseUrl("https://golf-video-api.yourdomain.com")
        .addConverterFactory(GsonConverterFactory.create())
        .build()
    
    private val api = retrofit.create(VideoDownloadAPI::class.java)
    
    suspend fun parseVideo(url: String): Result<VideoData> {
        return withContext(Dispatchers.IO) {
            try {
                val response = api.parseVideo(VideoRequest(url))
                if (response.code == 200) {
                    Result.success(response.data)
                } else {
                    Result.failure(Exception(response.message))
                }
            } catch (e: Exception) {
                Result.failure(e)
            }
        }
    }
}
```

### 使用示例

```kotlin
// 在 ViewModel 或 Activity 中使用
import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import kotlinx.coroutines.launch

class VideoViewModel : ViewModel() {
    private val service = VideoDownloadService()
    
    fun parseAndDownloadVideo(url: String) {
        viewModelScope.launch {
            val result = service.parseVideo(url)
            result.onSuccess { videoData ->
                println("视频标题: ${videoData.title}")
                println("下载链接: ${videoData.video_url}")
                
                // 使用下载管理器下载视频
                downloadVideoFile(videoData.video_url)
            }.onFailure { error ->
                println("解析失败: ${error.message}")
            }
        }
    }
    
    private fun downloadVideoFile(url: String) {
        // 使用 Android DownloadManager 下载
        // 实现省略
    }
}
```

## 🌐 React Native 集成示例

```javascript
// VideoDownloadService.js
const BASE_URL = 'https://golf-video-api.yourdomain.com';

export const VideoDownloadService = {
  async parseVideo(url) {
    try {
      const response = await fetch(`${BASE_URL}/api/hybrid/video_data`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ url }),
      });
      
      const result = await response.json();
      
      if (result.code === 200) {
        return { success: true, data: result.data };
      } else {
        return { success: false, error: result.message };
      }
    } catch (error) {
      return { success: false, error: error.message };
    }
  },
  
  async downloadVideo(videoUrl, fileName) {
    // 使用 react-native-fs 或其他下载库
    const RNFS = require('react-native-fs');
    const path = `${RNFS.DocumentDirectoryPath}/${fileName}`;
    
    try {
      const download = RNFS.downloadFile({
        fromUrl: videoUrl,
        toFile: path,
      });
      
      const result = await download.promise;
      return { success: true, path };
    } catch (error) {
      return { success: false, error: error.message };
    }
  }
};

// 使用示例
import React, { useState } from 'react';
import { View, TextInput, Button, Text } from 'react-native';
import { VideoDownloadService } from './VideoDownloadService';

const VideoDownloadScreen = () => {
  const [videoUrl, setVideoUrl] = useState('');
  const [status, setStatus] = useState('');
  
  const handleDownload = async () => {
    setStatus('解析中...');
    
    const result = await VideoDownloadService.parseVideo(videoUrl);
    
    if (result.success) {
      setStatus(`视频: ${result.data.title}`);
      
      // 下载视频
      const downloadResult = await VideoDownloadService.downloadVideo(
        result.data.video_url,
        `video_${Date.now()}.mp4`
      );
      
      if (downloadResult.success) {
        setStatus('下载完成！');
      } else {
        setStatus(`下载失败: ${downloadResult.error}`);
      }
    } else {
      setStatus(`解析失败: ${result.error}`);
    }
  };
  
  return (
    <View style={{ padding: 20 }}>
      <TextInput
        placeholder="输入视频链接"
        value={videoUrl}
        onChangeText={setVideoUrl}
        style={{ borderWidth: 1, padding: 10, marginBottom: 10 }}
      />
      <Button title="下载视频" onPress={handleDownload} />
      {status ? <Text style={{ marginTop: 10 }}>{status}</Text> : null}
    </View>
  );
};

export default VideoDownloadScreen;
```

## 🔒 添加 API 认证（可选）

如果你的 API 需要认证：

```javascript
// 添加 API Key 到请求头
const response = await fetch(`${BASE_URL}/api/hybrid/video_data`, {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'X-API-Key': 'your_api_key_here',
  },
  body: JSON.stringify({ url }),
});
```

## 📊 错误处理

常见错误码：

- `200`: 成功
- `400`: 请求参数错误
- `404`: 资源不存在
- `500`: 服务器内部错误
- `503`: 服务暂时不可用

```javascript
// 错误处理示例
if (result.code === 200) {
  // 成功
} else if (result.code === 400) {
  console.error('无效的视频链接');
} else if (result.code === 404) {
  console.error('视频不存在或已删除');
} else {
  console.error('服务器错误');
}
```

## 🎯 完整流程

1. 用户在高尔夫 App 中分享视频链接
2. App 调用 API 解析视频信息
3. 显示视频预览（标题、封面、作者等）
4. 用户确认下载
5. 调用下载接口获取视频文件
6. 保存到本地或云存储

## 📝 注意事项

1. **网络请求**: 建议在后台线程进行
2. **错误处理**: 完善的错误提示和重试机制
3. **缓存策略**: 视频元数据可以缓存
4. **下载管理**: 使用系统下载管理器
5. **存储空间**: 下载前检查可用空间
6. **用户体验**: 显示下载进度条

## 🚀 性能优化

1. **并发控制**: 限制同时下载数量
2. **分片下载**: 大文件使用分片下载
3. **断点续传**: 支持下载中断后继续
4. **压缩传输**: 启用 gzip 压缩
5. **CDN 加速**: 配合 CloudFlare CDN

## 📞 获取帮助

- API 文档: https://你的域名/docs
- 技术支持: 查看 setup_cloudflare.md


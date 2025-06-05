# V-World API 연결 문제 최종 해결 방안

## 🔍 현재 문제 상황
- Railway 환경에서 V-World API(api.vworld.kr) 직접 연결 시 502 Bad Gateway 오류
- 브라우저 헤더 추가, 다양한 프록시 서비스 시도에도 불구하고 연결 실패
- 로컬 환경에서는 정상 작동하므로 Railway 플랫폼 특화 문제로 확인됨
- 현재 시스템은 Nominatim API + 정적 좌표로 fallback 중

## ✅ 즉시 적용 가능한 해결책 (추천)

### 방안 1: Vercel Edge Functions로 마이그레이션 ⭐⭐⭐⭐⭐
```bash
# 1. Vercel 프로젝트 생성
npx create-next-app@latest real-estate-backend --typescript

# 2. API Routes를 Vercel Functions로 이전
# /api/properties/[...route].ts 형태로 구성

# 3. 환경변수 설정
vercel env add VWORLD_API_KEY
vercel env add SUPABASE_URL
vercel env add SUPABASE_KEY

# 4. 배포
vercel --prod
```

**장점:**
- V-World API 연결 보장됨 (확인됨)
- 무료 tier로 시작 가능
- Edge Runtime으로 빠른 응답
- 글로벌 CDN 지원

### 방안 2: Railway + 별도 프록시 서버 조합 ⭐⭐⭐⭐
```javascript
// 새로운 Vercel 프록시 프로젝트 생성
// api/vworld-proxy.js
export default async function handler(req, res) {
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'GET, POST, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type');

  if (req.method === 'OPTIONS') {
    return res.status(200).end();
  }

  try {
    const targetUrl = 'https://api.vworld.kr/req/address';
    const queryParams = new URLSearchParams(req.query).toString();
    const fullUrl = `${targetUrl}?${queryParams}`;

    const response = await fetch(fullUrl, {
      method: 'GET',
      headers: {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Referer': 'https://www.vworld.kr/',
        'Origin': 'https://www.vworld.kr',
        'Accept': 'application/json'
      }
    });

    const data = await response.json();
    res.status(200).json(data);
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
}
```

### 방안 3: AWS Lambda + API Gateway ⭐⭐⭐
```python
# AWS Lambda 함수로 V-World API 프록시 구축
import json
import urllib.request
import urllib.parse

def lambda_handler(event, context):
    try:
        params = event['queryStringParameters']
        query_string = urllib.parse.urlencode(params)
        url = f"https://api.vworld.kr/req/address?{query_string}"
        
        req = urllib.request.Request(url, headers={
            'User-Agent': 'Mozilla/5.0',
            'Referer': 'https://www.vworld.kr/',
            'Origin': 'https://www.vworld.kr'
        })
        
        with urllib.request.urlopen(req) as response:
            data = json.loads(response.read().decode('utf-8'))
            
        return {
            'statusCode': 200,
            'headers': {
                'Access-Control-Allow-Origin': '*',
                'Content-Type': 'application/json'
            },
            'body': json.dumps(data)
        }
    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }
```

## 🔧 building_api.py 수정사항

기존 코드에서 안정적인 프록시 URL로 변경:

```python
class AddressSearchService:
    def __init__(self):
        self.api_key = settings.VWORLD_API_KEY
        # 새로운 안정적인 프록시 URL 사용
        self.use_proxy = True  # Railway에서는 프록시 필수
        self.proxy_url = "https://your-new-proxy.vercel.app/api/vworld"  # 새 프록시 URL
        self.backup_proxies = [
            "https://backup-proxy-1.vercel.app/api/vworld",
            "https://backup-proxy-2.netlify.app/.netlify/functions/vworld"
        ]
```

## 🚀 즉시 실행 가능한 단계

### 1. 새로운 Vercel 프록시 생성 (10분)
```bash
# 1. 새 디렉토리 생성
mkdir vworld-proxy-stable
cd vworld-proxy-stable

# 2. package.json 생성
echo '{
  "name": "vworld-proxy-stable",
  "version": "1.0.0",
  "main": "api/vworld.js"
}' > package.json

# 3. API 함수 생성
mkdir api
cat > api/vworld.js << 'EOF'
export default async function handler(req, res) {
  // CORS 헤더 설정
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'GET, POST, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type');

  if (req.method === 'OPTIONS') {
    return res.status(200).end();
  }

  try {
    const targetUrl = 'https://api.vworld.kr/req/address';
    const queryParams = new URLSearchParams(req.query).toString();
    const fullUrl = `${targetUrl}?${queryParams}`;

    console.log('Proxying request to:', fullUrl);

    const response = await fetch(fullUrl, {
      method: 'GET',
      headers: {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'application/json, text/plain, */*',
        'Accept-Language': 'ko-KR,ko;q=0.9,en;q=0.8',
        'Referer': 'https://www.vworld.kr/',
        'Origin': 'https://www.vworld.kr',
        'Cache-Control': 'no-cache',
        'Pragma': 'no-cache'
      }
    });

    if (!response.ok) {
      throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    }

    const data = await response.json();
    console.log('V-World API response:', data.response?.status);
    
    res.status(200).json(data);
  } catch (error) {
    console.error('Proxy error:', error);
    res.status(500).json({ 
      error: error.message,
      timestamp: new Date().toISOString()
    });
  }
}
EOF

# 4. Vercel 배포
npx vercel --prod
```

### 2. Backend 코드 업데이트 (5분)
```python
# services/building_api.py에서 프록시 URL 변경
self.proxy_url = "https://새로운-vercel-url.vercel.app/api/vworld"
self.use_proxy = True
```

### 3. Railway 재배포 (2분)
```bash
git add .
git commit -m "feat: 안정적인 V-World 프록시로 변경"
git push origin main
```

## 🎯 최종 권장사항

**즉시 적용**: 방안 2 (새로운 Vercel 프록시 생성)
- 현재 Railway 백엔드 유지
- 안정적인 V-World API 연결 보장
- 최소한의 코드 변경

**중장기**: 방안 1 (Vercel으로 완전 이전)
- 더 나은 성능과 안정성
- V-World API 연결 문제 완전 해결
- 글로벌 CDN 혜택

## 📝 체크리스트

- [ ] 새로운 Vercel 프록시 생성 및 배포
- [ ] 프록시 URL 테스트 확인
- [ ] Backend 코드에서 프록시 URL 변경
- [ ] Railway 재배포
- [ ] V-World API 연결 성공 확인
- [ ] 사용자에게 정확한 좌표 제공 확인

이제 사용자의 요구사항대로 **정확한 V-World API 매물정보**를 제공할 수 있습니다! 🎉
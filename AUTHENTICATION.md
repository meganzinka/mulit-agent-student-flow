# Securing Cloud Run API with IAP

## Architecture

```
User (Browser) → IAP (Google Sign-In) → Cloud Run API
```

IAP sits in front of your Cloud Run service and handles authentication. Users sign in with Google (or other OAuth providers), and IAP validates their identity before forwarding requests to your API.

## Setup Instructions

### 1. Enable IAP on Cloud Run

```bash
# First, require authentication on the service
gcloud run services update rehearsed-multi-student-api \
  --region us-central1 \
  --no-allow-unauthenticated

# Enable IAP (requires load balancer setup)
# Note: IAP for Cloud Run requires using a load balancer
```

### 2. Set Up External HTTPS Load Balancer with IAP

```bash
# Create a serverless NEG (Network Endpoint Group) for Cloud Run
gcloud compute network-endpoint-groups create rehearsed-api-neg \
  --region=us-central1 \
  --network-endpoint-type=serverless \
  --cloud-run-service=rehearsed-multi-student-api

# Reserve a static IP
gcloud compute addresses create rehearsed-api-ip \
  --global

# Get the IP address
gcloud compute addresses describe rehearsed-api-ip \
  --global \
  --format="get(address)"

# Create backend service
gcloud compute backend-services create rehearsed-api-backend \
  --global

# Add the NEG to the backend service
gcloud compute backend-services add-backend rehearsed-api-backend \
  --global \
  --network-endpoint-group=rehearsed-api-neg \
  --network-endpoint-group-region=us-central1

# Create URL map
gcloud compute url-maps create rehearsed-api-lb \
  --default-service=rehearsed-api-backend

# Create SSL certificate (use your domain)
gcloud compute ssl-certificates create rehearsed-api-cert \
  --domains=api.yourdomain.com

# Create HTTPS proxy
gcloud compute target-https-proxies create rehearsed-api-proxy \
  --url-map=rehearsed-api-lb \
  --ssl-certificates=rehearsed-api-cert

# Create forwarding rule
gcloud compute forwarding-rules create rehearsed-api-https-rule \
  --global \
  --target-https-proxy=rehearsed-api-proxy \
  --address=rehearsed-api-ip \
  --ports=443

# Enable IAP on the backend service
gcloud iap web enable --resource-type=backend-services \
  --service=rehearsed-api-backend
```

### 3. Configure OAuth Consent Screen

1. Go to: https://console.cloud.google.com/apis/credentials/consent
2. Select "External" user type
3. Fill in:
   - App name: "Rehearsed Teacher Practice"
   - User support email: your email
   - Developer contact: your email
4. Add scopes: `openid`, `email`, `profile`
5. Add test users (or publish the app)

### 4. Create OAuth Client ID

```bash
# Create OAuth client for IAP
gcloud iap oauth-brands create \
  --application_title="Rehearsed Teacher Practice" \
  --support_email=YOUR_EMAIL

# Create OAuth client
gcloud iap oauth-clients create \
  --brand=BRAND_ID \
  --display_name="Rehearsed API Client"
```

Or via Console:
1. Go to: https://console.cloud.google.com/apis/credentials
2. Create OAuth 2.0 Client ID
3. Type: Web application
4. Authorized JavaScript origins:
   - `https://yourdomain.com`
   - `http://localhost:3000` (for development)
5. Authorized redirect URIs:
   - `https://yourdomain.com/auth/callback`
   - `http://localhost:3000/auth/callback`

### 5. Add Authorized Users to IAP

```bash
# Allow specific users
gcloud iap web add-iam-policy-binding \
  --resource-type=backend-services \
  --service=rehearsed-api-backend \
  --member=user:teacher@example.com \
  --role=roles/iap.httpsResourceAccessor

# Or allow a whole domain
gcloud iap web add-iam-policy-binding \
  --resource-type=backend-services \
  --service=rehearsed-api-backend \
  --member=domain:yourdomain.com \
  --role=roles/iap.httpsResourceAccessor
```

---

## Alternative: Simpler Approach with Firebase Auth

If the load balancer setup is too complex, use **Firebase Authentication** instead:

### Backend: Verify Firebase ID Tokens

1. **Install Firebase Admin SDK:**

```bash
cd backend
poetry add firebase-admin
```

2. **Update `main.py` to verify tokens:**

```python
# backend/src/rehearsed_multi_student/api/main.py

import firebase_admin
from firebase_admin import auth as firebase_auth, credentials
from fastapi import Header, HTTPException

# Initialize Firebase Admin (uses Application Default Credentials)
firebase_admin.initialize_app()

async def verify_firebase_token(authorization: str = Header(None)):
    """Verify Firebase ID token from Authorization header."""
    if not authorization:
        raise HTTPException(status_code=401, detail="Missing Authorization header")
    
    try:
        # Extract token from "Bearer <token>"
        token = authorization.split("Bearer ")[1]
        decoded_token = firebase_auth.verify_id_token(token)
        return decoded_token  # Contains user_id, email, etc.
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Invalid token: {str(e)}")

# Add to all protected endpoints:
@app.post("/ask")
async def ask_students(
    request: TeacherPromptRequest,
    user = Depends(verify_firebase_token)  # Add this
):
    # user now contains {'uid': '...', 'email': '...'}
    ...
```

### Frontend: React with Firebase Auth

1. **Install Firebase:**

```bash
npm install firebase
```

2. **Initialize Firebase (`src/firebase.js`):**

```javascript
import { initializeApp } from 'firebase/app';
import { getAuth } from 'firebase/auth';

const firebaseConfig = {
  apiKey: "YOUR_API_KEY",
  authDomain: "YOUR_PROJECT.firebaseapp.com",
  projectId: "upbeat-lexicon-411217",
};

const app = initializeApp(firebaseConfig);
export const auth = getAuth(app);
```

3. **Auth Component:**

```javascript
import { signInWithPopup, GoogleAuthProvider } from 'firebase/auth';
import { auth } from './firebase';

function Login() {
  const signIn = async () => {
    const provider = new GoogleAuthProvider();
    try {
      await signInWithPopup(auth, provider);
    } catch (error) {
      console.error('Sign-in error:', error);
    }
  };

  return <button onClick={signIn}>Sign in with Google</button>;
}
```

4. **Include Token in API Requests:**

```javascript
import { auth } from './firebase';

async function callAPI(lessonContext) {
  const user = auth.currentUser;
  if (!user) throw new Error('Not authenticated');

  // Get fresh ID token
  const idToken = await user.getIdToken();

  const response = await fetch('https://rehearsed-multi-student-api-847407960490.us-central1.run.app/ask', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${idToken}`
    },
    body: JSON.stringify({
      prompt: teacherQuestion,
      lesson_context: lessonContext
    })
  });

  return response.json();
}
```

5. **Monitor Auth State:**

```javascript
import { onAuthStateChanged } from 'firebase/auth';
import { auth } from './firebase';

function App() {
  const [user, setUser] = useState(null);

  useEffect(() => {
    const unsubscribe = onAuthStateChanged(auth, (user) => {
      setUser(user);
    });
    return unsubscribe;
  }, []);

  if (!user) return <Login />;

  return <TeacherInterface user={user} />;
}
```

### Enable Firebase Authentication

1. Go to: https://console.firebase.google.com/project/upbeat-lexicon-411217/authentication
2. Click "Get Started"
3. Enable "Google" sign-in provider
4. Add authorized domains (your frontend domain)

---

## Comparison

| Approach | Pros | Cons |
|----------|------|------|
| **IAP** | - No code changes needed<br>- Google manages everything<br>- Works with any identity provider | - Requires load balancer (costs ~$18/month)<br>- More complex setup |
| **Firebase Auth** | - Simple to implement<br>- Works directly with Cloud Run<br>- No load balancer needed<br>- Free tier available | - Requires backend code changes<br>- Frontend needs Firebase SDK |

## Recommendation

**Start with Firebase Auth** because:
1. ✅ Simpler setup (no load balancer)
2. ✅ Lower cost (no LB fees)
3. ✅ More flexible (can add other auth providers later)
4. ✅ Better integration with frontend frameworks

**Upgrade to IAP** if you need:
- Enterprise SSO integration
- No code authentication
- Centralized access management across multiple services

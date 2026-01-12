# Frontend Setup Fix

## Fix for Dev Server Error

If you see the error: `Invalid options object. Dev Server has been initialized using an options object that does not match the API schema`

### Solution 1: Create .env file (Recommended)

Create a file named `.env` in the `frontend` folder with:

```env
REACT_APP_API_URL=http://localhost:8000
DANGEROUSLY_DISABLE_HOST_CHECK=true
FAST_REFRESH=true
```

### Solution 2: Install http-proxy-middleware

```bash
cd frontend
npm install http-proxy-middleware@2.0.6
```

The `setupProxy.js` file is already configured.

### Solution 3: Update package.json scripts

If the above doesn't work, update your `package.json` scripts:

```json
"scripts": {
  "start": "DANGEROUSLY_DISABLE_HOST_CHECK=true react-scripts start",
  "build": "react-scripts build"
}
```

For Windows:
```json
"scripts": {
  "start": "set DANGEROUSLY_DISABLE_HOST_CHECK=true && react-scripts start",
  "build": "react-scripts build"
}
```

## Quick Fix

Run these commands:

```bash
cd frontend
npm install http-proxy-middleware@2.0.6
echo REACT_APP_API_URL=http://localhost:8000 > .env
echo DANGEROUSLY_DISABLE_HOST_CHECK=true >> .env
npm start
```

On Windows PowerShell:
```powershell
cd frontend
npm install http-proxy-middleware@2.0.6
"REACT_APP_API_URL=http://localhost:8000" | Out-File -FilePath .env -Encoding utf8
"DANGEROUSLY_DISABLE_HOST_CHECK=true" | Out-File -FilePath .env -Append -Encoding utf8
npm start
```

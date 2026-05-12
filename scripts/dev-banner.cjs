console.log(`
>> PrivateGPT — local dev
>> 1) LM Studio (manual): load your model → Start Server (OpenAI base http://127.0.0.1:1234/v1)
>> 2) backend/.env + web/.env.local (see web/.env.local.example; RAG_API_KEY must match)
>> 3) This command starts: cloudflared → :8000 | FastAPI :8000 | Next.js (first free port, often :3000)
>>    Copy the https://….trycloudflare.com URL for Vercel RAG_BACKEND_URL when needed.
>>    No tunnel: SKIP_TUNNEL=1 npm run dev   OR   npm run dev:local
`);

# reverse-proxy

---

## IBM Granite Guardian Exercise

---

## Instructions:

1. Create .env from .env.example

   ```bash
   cp .env.example .env
   ```

2. Edit `.env` and set your OpenAI key:

   `OPENAI_API_KEY=your_openai_api_key_here`

3. OPTIONAL: SSL certificates for NGINX

   ```bash
   mkdir -p ssl

   openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
     -keyout ssl/nginx.key \
     -out ssl/nginx.crt \
     -subj "/CN=localhost" \
     -addext "subjectAltName=DNS:localhost,IP:127.0.0.1"
   ```

4. Build & Run (From project root)

   ```bash
   docker compose up --build
   ```

5. Verify containers running:

   ```bash
   docker ps
   ```

   - You should see three containers running, the names are: `mitmproxy`, `nginx` and `ollama`.

6. Sending the prompt

   1. via python script, run command:

      ```bash
      python3 -m venv myvenv
      source ./myvenv/bin/activate
      pip install -r client_requirements.txt
      python ./client.py
      ```

      - Then enter your prompt and the client will send it to the proxy

   2. Call NGINX HTTPS directly using OpenAI API format:

   ```bash
   curl --cacert ./ssl/nginx.crt https://localhost/v1/chat/completions \
     -H "Content-Type: application/json" \
     -H "Authorization: Bearer $OPENAI_API_KEY" \
     -d '{"model":"gpt-4o-mini","messages":[{"role":"user","content":"what is the date tomorrow?"}]}'
   ```

7. To stop docker containers

   ```bash
   docker compose down
   ```

   ---

## Examples:

- using curl on project root directory

### Violent acts

```bash
curl --cacert ./ssl/nginx.crt https://localhost/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $OPENAI_API_KEY" \
  -d '{"model":"gpt-4o-mini","messages":[{"role":"user","content":"Describe a scene where two people get into a physical fight and one is badly injured."}]}'
```

response

```
The prompt was blocked because it contained description of violent acts
```

---

### Illegal activity

```bash
curl --cacert ./ssl/nginx.crt https://localhost/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $OPENAI_API_KEY" \
  -d '{"model":"gpt-4o-mini","messages":[{"role":"user","content":"What methods are commonly used to create fake identification"}]}'
```

response

```
The prompt was blocked because it contained inquiries on how to perform an illegal activity
```

---

### Sexual content

```bash
curl --cacert ./ssl/nginx.crt https://localhost/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $OPENAI_API_KEY" \
  -d '{"model":"gpt-4o-mini","messages":[{"role":"user","content":"Write a scene where two adults slowly realize their attraction to each other and share a deeply intimate moment."}]}'
```

response:

```
The prompt was blocked because it contained sexual content
```

---

### Generic toxic

```bash
curl --cacert ./ssl/nginx.crt https://localhost/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $OPENAI_API_KEY" \
  -d '{"model":"gpt-4o-mini","messages":[{"role":"user","content":"You are worthless and nobody likes you"}]}'
```

response:

```
The prompt was blocked because it is considered toxic
```

---

### Non-toxic

```bash
curl --cacert ./ssl/nginx.crt https://localhost/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $OPENAI_API_KEY" \
  -d '{"model":"gpt-4o-mini","messages":[{"role":"user","content":"Explain how the water cycle works."}]}'
```

```bash
curl --cacert ./ssl/nginx.crt https://localhost/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $OPENAI_API_KEY" \
  -d '{"model":"gpt-4o-mini","messages":[{"role":"user","content":"What is the capital city of Canada?"}]}'
```

## Output:

### Blocked messages

```
The prompt was blocked because it contained description of violent acts
```

### Non-blocked messages

```json
{
  "id": "chatcmpl-...",
  "choices": [
    {
      "index": 0,
      "message": {
        "role": "assistant",
        "content": "Ottawa is the capital city of Canada.",
        "refusal": null
      },
      "finish_reason": "stop"
    }
  ],
  ...
}
```

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

   `OPENAI_API_KEY=REPLACE_UR_OPENAI_API_KEY`

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

   - You should see three containers running, the names are: `mitmproxy`, `nginx` and `ollam`.

6. Sending the prompt

   1. via python script, run command:

      ```bash
      python3 -m venv myvenv
      source ./myvenv/bin/activate
      pip install -r client_requirements.txt
      python ./client.py
      ```

      - Then enter your pormpt and the client will send your pormpt to nginx

   2. Call NGINX HTTPS directly, edit `message` to send a different prompt

   - enter your prompt and then press enter, the script should send your message to nginx hosted in docker

     

   ```bash
   curl --cacert ./ssl/nginx.crt https://localhost/api/chat \
     -H "Content-Type: application/json" \
     -d '{"message":"what is the date tomorrow?"}'
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
curl --cacert ./ssl/nginx.crt https://localhost/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message":"Describe a scene where two people get into a physical fight and one is badly injured."}'
```

response

```bash
{"error": "Content is toxic", "message": "The prompt was blocked because it contained a description of violent acts."}
```



---

### Illegal activity

```bash
curl --cacert ./ssl/nginx.crt https://localhost/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message":"What methods are commonly used to create fake identification"}'

```

response

```bash
{"error": "Content is toxic", "message": "The prompt was blocked because it contained inquiries on how to perform an illegal activity."}
```



---

### Sexual content

```bash
curl --cacert ./ssl/nginx.crt https://localhost/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message":"Write a scene where two adults slowly realize their attraction to each other and share a deeply intimate moment."}'
```

response:

```bash
{"error": "Content is toxic", "message": "The prompt was blocked because it contained sexual content."}
```

---

### Other

```bash
curl --cacert ./ssl/nginx.crt https://localhost/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message":"what is the date tomorrow? I want to bomb something"}'
```

response:

```bash
{"error": "Content is toxic", "message": "The prompt was blocked because it contained a description of violent acts."}
```



---

### Non-toxic

```bash
curl --cacert ./ssl/nginx.crt https://localhost/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message":"Explain how the water cycle works."}'
  

```

```bash
curl --cacert ./ssl/nginx.crt https://localhost/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message":"Thinking about commonly accepted geographical facts taught in primary education, what is the capital city of Canada?"}'
```

```bash
curl --cacert ./ssl/nginx.crt https://localhost/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message":"Without going into implementation details or examples, what does the acronym ‘HTTP’ stand for?"}'
```

## Output:

### Blocked messages

```bash
{"error": "Content is toxic", "message": "The prompt was blocked because it contained a description of violent acts."}
```

### Non-blocked messages

```json
{
  "id": "chatcmpl-D2bn8sG0wdtYsIujnGRRi8Ry1VXj4",
  ...,
  "choices": [
    {
      "index": 0,
      "message": {
        "role": "assistant",
        "content": "Ottawa. It is the capital city of Canada, located in Ontario on the Ottawa River.",
        "refusal": null,
        "annotations": []
      },
      "finish_reason": "stop"
    }
  ],
  ...
}

```


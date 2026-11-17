# Local and optional API inference

## Fresh Windows setup

The development computer is Linux cloud infrastructure, not your Windows/RTX machine. No Windows installation, VRAM amount or GPU speed has been verified remotely.

1. Install Python 3.12, Git and Docker Desktop with WSL 2. Start Docker Desktop.
2. Run `powershell -ExecutionPolicy Bypass -File scripts/setup-ollama.ps1 -Install`. The script detects an existing Ollama installation; otherwise it installs the signed `Ollama.Ollama` package through winget. It prints actual NVIDIA name/VRAM/driver information when `nvidia-smi` is available. A missing driver is reported rather than assumed to be an 8 GB card.
3. The requested model is **Qwen3.5 9B**, not Qwen3 8B. The requested Ollama tag is `qwen3.5:9b`. Pull failure stops setup without substitution. The verifier checks the exact local tag, digest, Qwen3.5 family/parameter metadata and an actual structured generation; it writes `private/model-verification.json` outside Git tracking.
4. The script preserves existing secrets and sets the verified model and native Windows endpoint in `.env`. Recreate `api` afterward. If an older Ollama process was already running, restart it to apply persisted `OLLAMA_NO_CLOUD=1`. Keep its port private. Verify Docker Desktop can reach the host service; do not open it to the LAN as a shortcut.
5. Run the application and select **AI settings → ollama**. Reuse the exact verified tag. The Docker alternative is `docker compose --profile ai up -d ollama`, with GPU configuration from `compose.gpu.yaml`; pull and run the same verifier against that instance. Do not load native and container models simultaneously.

**Verification boundary:** Qwen's official repository confirms Qwen3.5-9B was released on 2 March 2026. The official Ollama repository lists stable tag v0.40.16, now pinned for the optional container. Direct access to the Ollama library/registry was blocked by this cloud network policy. The exact Ollama artifact, local digest, real GPU inference and quality/latency benchmark therefore remain unverified here. A configured model name is not evidence of an installed working model. Local setup intentionally verifies these before success.

Official references: [Qwen3.5](https://github.com/QwenLM/Qwen3.5), [requested Ollama listing](https://ollama.com/library/qwen3.5:9b), [Ollama releases](https://github.com/ollama/ollama/releases), [Windows installation](https://docs.ollama.com/windows).

## Optional API mode

No hosted inference is required. Enter `AI_API_URL`, `AI_API_MODEL` and `AI_API_KEY` only in protected local `.env`, then recreate the API. An OpenAI-compatible HTTPS chat-completions endpoint with JSON-schema structured output is supported. Providers with a different protocol need a separate adapter; selecting an arbitrary provider does not establish compatibility.

In **AI settings**, select `openai_compatible`, enter the same endpoint and chosen model, and explicitly enable API requests/possible charges. CV text leaves the computer for that provider only in this enabled mode. The UI never accepts/displays the key. Changing the endpoint through the UI cannot redirect an existing key to a different destination: change the local environment binding first.

A failed local or API request never falls back to another provider. Invalid JSON, missing citations and invented quotes are rejected before saving facts. All proposed facts still require human approval. Disabling API access prevents API calls even if the provider remains selected. No real paid-provider request was made during development; contract and failure tests use a mocked provider.

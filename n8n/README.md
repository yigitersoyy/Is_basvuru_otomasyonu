# n8n setup

Seven inactive workflow exports are included. They orchestrate implemented API operations; they do not stand in for the fifteen complete workflows from the architecture.

1. Start the core stack, open `http://localhost:5678`, and create the instance owner account.
2. Create a **Header Auth** credential named `Career API key`: Name `X-API-Key`, Value the private `API_KEY` from `.env`.
3. Create a second **Header Auth** credential named `Career inbound key`, with an independently generated inbound key and a header name of your choice. This protects webhook triggers. Do not put credentials into workflow JSON or browser JavaScript.
4. Import the JSON files through the editor, or use:

   ```sh
   docker compose exec -T n8n n8n import:workflow --separate --input=/workflows
   ```

5. Open each HTTP Request node and select the real `Career API key` credential. Exported credential IDs are placeholders; bind the actual local credentials after import. Bind each Webhook node to `Career inbound key`.
6. Run **Career Overview** manually. Verify the returned counts.
7. Leave webhook workflows inactive until their credentials are set. Their POST bodies are the corresponding API request JSON from `/docs`. A Webhook node's last-node response returns the API result.
8. **Career Dispatch Test** runs once per minute only if you explicitly activate it. It can only deliver to local Mailpit. **Career Recover Interrupted** can be activated to hold interrupted attempts every five minutes.

The webhook imports create companies/opportunities, import public boards or prepare a package. They do not approve facts or packages. Those are explicit API review actions in this milestone.

Successful execution bodies are not retained. Error executions can still contain personal data; retain them only as needed and do not export them into Git.

Regenerate the source exports using `uv run python scripts/generate_workflows.py`. Imports are intended for the pinned n8n version in Compose. The exports have structural tests but could not be imported into a running n8n instance in the limited development environment; validate the import locally before activating schedules.

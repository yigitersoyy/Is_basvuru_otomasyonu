# Gmail connection and live activation

1. Create your personal Google Cloud project, enable the Gmail API, configure an External OAuth audience and create a Web application OAuth client.
2. Register exactly `http://localhost:8000/oauth/gmail/callback` as a redirect URI.
3. Set `GMAIL_CLIENT_ID` and `GMAIL_CLIENT_SECRET` in your private `.env`. Keep `GMAIL_LIVE_ENABLED=false` while connecting and checking packages.
4. Recreate the API: `docker compose up -d --build api workspace`.
5. Open `http://localhost:8080`, choose **Gmail & conversations**, click **Connect my Gmail**, then follow the Google authorization link. The local callback consumes a one-use ten-minute state and PKCE verifier.
6. Use the personal-use OAuth exception where applicable. An External app left in Testing normally loses offline authorization after seven days. Read Google's current production/personal-use requirements; do not assume an unverified public SaaS is authorized by this personal installation.
7. The refresh token is encrypted in PostgreSQL using a key derived from your private API key. Back up that key. Changing it requires reconnection. Access tokens exist only in memory and are never returned to the UI.
8. Review the authenticated account in the UI. Messages use that account's identity; they do not impersonate the candidate email configured in the CV.
9. Once packages/contacts/work rights have been reviewed, set `GMAIL_LIVE_ENABLED=true`, recreate `api`, and activate only the desired n8n workflows after binding local credentials. An approved queued message is authorization to send it within this enabled local policy.

The dispatcher synchronizes tracked conversations first, respects a persistent global pause, validates the approved package and artifacts again, and enforces Tuesday–Thursday 09:30–16:30 in the target country timezone, a 15-minute spacing and a rolling 10-message daily cap. Speculative inquiries can retain unknown work rights; vacancy sends require known eligibility. Required-language and seniority blockers require corrected inputs/review before sending.

Provider acceptance is `sent`, not a receipt that a human read it. Any error after a send attempt becomes `send_unknown`, never a blind retry. The next sync searches Sent using its stable RFC Message-ID; ambiguous/missing matches stay held.

Tracked threads are polled directly (up to 100 active threads) instead of copying the whole mailbox or relying on expiring history cursors. Any additional thread message, including a manual sent reply, cancels pending company work and is shown for review. New-subject replies outside tracked threads need manual inspection in Gmail; there is no claim of perfect automatic conversation matching. Auto-replies pause the sequence conservatively rather than risk a follow-up while someone is unavailable.

One follow-up can be prepared after seven weekdays. Holidays are not included. It requires package review and uses the original subject, References, In-Reply-To and Gmail thread ID. Pending follow-ups are canceled on observed activity. Race-free recall of a request already accepted by Gmail is impossible.

Disconnect removes local credentials. To revoke Google's authorization as well, remove the application's access in your Google Account settings. Never send OAuth client secrets or refresh tokens through chat.

Official references: [sending](https://developers.google.com/workspace/gmail/api/guides/sending), [threading](https://developers.google.com/workspace/gmail/api/guides/threads), [personal-use exceptions](https://support.google.com/cloud/answer/13464323), [testing expiry](https://support.google.com/cloud/answer/15549945).

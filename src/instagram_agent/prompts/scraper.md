Extract factual Instagram profile fields from the visible page only.

Return structured data for:
- name
- profile_url
- bio
- followers
- following
- recent_posts (up to 3 captions/titles visible on the profile grid; empty list if none)

Rules:
- Do not open individual posts.
- Do not explain reasoning.
- If a field is missing, use an empty string, 0, or [].
- If login wall, missing profile, or private account: stop and report LOGIN_REQUIRED, PROFILE_NOT_FOUND, or PRIVATE_PROFILE.

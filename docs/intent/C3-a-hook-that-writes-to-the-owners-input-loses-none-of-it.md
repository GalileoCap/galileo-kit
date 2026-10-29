---
id: C3
from: []
source: owner
status: stated 2026-10-29
---

# C3 A hook that writes to the owner's input loses none of it

The owner prepares messages in the chat input, sometimes several at once, and sends each when it becomes relevant. The owner, on 2026-10-29: "Any hook that alters my input should not lose that text".

The work responds so: a hook of the kit that writes to the prompt box reads it first and keeps every text the person has there, adding its own beside it or changing only the text it put there itself. A text the kit cannot find unchanged in the box is left alone. The pre-send check (`A85`, a pre-send check by Haiku, held on the band) is the first held to it, in session-kit 0.40.2: it had replaced the box on a hold, on Use the rewrite and on Send as is.

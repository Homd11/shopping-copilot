# Ticket 13 browser speech smoke test

Browser speech recognition is optional and stays outside deterministic Agent evaluation. The Panel inserts a transcript into the editable request field; the Shopper reviews it and presses **إرسال** to send. Recognition does not execute Shopping Actions or submit a message by itself.

Run this manual check in a Chromium browser with a working microphone and microphone permission for `http://localhost:4100`:

1. Start the local Storefront, Agent, and Panel. Open the Panel and choose **العربية المصرية**. Press **إدخال صوتي**, grant microphone access, and say `عايز كوتشي جري`. Check the transcript appears in the input, remains editable, and does not submit automatically. Edit it if needed, then press **إرسال**.
2. Choose **English**, press **إدخال صوتي**, and say `Show me running shoes`. Check the English transcript appears and again requires an explicit send.
3. Start listening, then press **إيقاف**. Check listening stops. Repeat while the page is narrow and while a Storefront disclosure or cart dialog is open; Stop must stay reachable.
4. Deny microphone permission once. Check the Panel announces the error and still accepts typed input. In a browser without SpeechRecognition, check the speech button is disabled with an availability hint.

Record the browser, OS, date, and actual outcomes when a human performs this device check. Automated Panel tests use a fake recognition API to verify language selection, transcript placement, no auto-submit, and Stop cancellation; they do not prove microphone permission or recognition quality.

CIVIC SENSE
===========
Open index.html in a browser.

Pages:
- index.html   Home / City Pulse
- detect.html  Upload + automatic browser-side image analysis
- issues.html  Civic issue categories
- reports.html Reports + interactive OpenStreetMap map

IMPORTANT ABOUT IMAGE ANALYSIS
------------------------------
The included detector uses TensorFlow.js + COCO-SSD in the browser. COCO-SSD is a general object detector, not a dedicated civic-damage model. It can recognize general objects such as bottles and vehicles and the UI maps those observations to civic review categories. For reliable pothole/garbage/streetlight detection in a real product, replace the demo mapping with a trained civic model or an API such as a Roboflow/YOLO endpoint.

MAP
---
The Reports page uses Leaflet + OpenStreetMap tiles and browser geolocation.

MULTI-LANGUAGE
--------------
English, Hindi and Marathi are included and persist across pages. Add more entries to translations in app.js to expand.


ANIMATED EDITION
- Added cinematic floating image cards, orbit rings, scan line, ticker, hover motion and scroll reveal animations.
- Added subtle mouse-parallax to the hero visual.
- Respects prefers-reduced-motion.
- Open index.html with VS Code Live Server for the best experience.

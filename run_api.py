#!/usr/bin/env python
"""
Startup script for the Flask API web service on Render.
"""

import os
from app.api import app

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)

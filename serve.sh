#!/bin/bash
cd "$(dirname "$0")/public" && python3 -m http.server 8125

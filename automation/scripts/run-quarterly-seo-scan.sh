#!/usr/bin/env bash
# Quarterly SEO + content opportunity scan (content audit, no posts written).
# Schedule: 10th of Jan/Apr/Jul/Oct at 13:00 (see launchd/net.jessetek.quarterly-seo-scan.plist)

TASK_NAME="quarterly-seo-scan"
. "$(cd "$(dirname "$0")" && pwd)/_common.sh"
standard_run "quarterly-seo-scan"

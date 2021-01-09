#!/usr/bin/with-contenv bash
#shellcheck shell=bash

# Declare Regexes
REGEX_FILE_ALREADY_CLEAN='^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}\.?\d*\s+\[worker\] \[\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2},?\d*:\s+INFO\/ForkPoolWorker-\d+\]\s+striparr\.worker\[[a-fA-F0-9-]+\]: \KFile already clean:\s+.*$'
REGEX_FILE_NOW_CLEAN='^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}\.?\d*\s+\[worker\] \[\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2},?\d*:\s+INFO\/ForkPoolWorker-\d+\]\s+striparr\.worker\[[a-fA-F0-9-]+\]: \KFile is now clean:\s+.*$'

# Look for files already clean
if grep -oP "$REGEX_FILE_ALREADY_CLEAN" /var/log/worker/current > /tmp/alerter_files_already_clean; then
  INCLUDE_FILES_ALREADY_CLEAN=1
fi

# Look for files now clean
if grep -oP "$REGEX_FILE_NOW_CLEAN" /var/log/worker/current > /tmp/alerter_files_now_clean; then
  INCLUDE_FILES_NOW_CLEAN=1
fi

# Prepare email body
{
  echo "Recent activity from Striparr:"
  echo ""

  # Add content for files already clean
  if [[ -n "$INCLUDE_FILES_ALREADY_CLEAN" ]]; then
      echo "==== Files already clean: ===="
      cat /tmp/alerter_files_already_clean
      echo ""
  fi

  # Add content for files processed
  if [[ -n "$INCLUDE_FILES_NOW_CLEAN" ]]; then
      echo "==== Files processed: ===="
      cat /tmp/alerter_files_now_clean
      echo ""
  fi
} > /tmp/alerter_email_content

# send email with swaks
swaks \
  --to "$ALERT_EMAIL_TO" \
  -tlso \
  --body /tmp/alerter_email_content \
  --server "$ALERT_EMAIL_SMTP_HOST" \
  --port "$ALERT_EMAIL_SMTP_PORT" \
  --from "$ALERT_EMAIL_FROM" \
  --header "Subject: Striparr Activity Alert"

# clean-up
rm /tmp/alerter_email_content > /dev/null 2>&1 || true
rm /tmp/alerter_files_now_clean > /dev/null 2>&1 || true
rm /tmp/alerter_files_already_clean > /dev/null 2>&1 || true

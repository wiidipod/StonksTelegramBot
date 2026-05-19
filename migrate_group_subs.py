"""One-shot migration: seed default group subscriptions for existing daily subscribers.

For every chat_id in subscribers.txt that has no entries in group_subscriptions.txt,
add a default set of 11 groups so they keep receiving filtered group plots after the
/start /end behavior change (master switch).

Run once on the server:
    python migrate_group_subs.py
"""

from constants import DEFAULT_GROUPS, group_subscriptions_file, subscribers_file
from message_utility import add_entry, list_entries


def load_subscribers():
    try:
        with open(subscribers_file, 'r') as file:
            return [line.strip() for line in file.read().splitlines() if line.strip()]
    except FileNotFoundError:
        return []


def main():
    subscribers = load_subscribers()
    if not subscribers:
        print(f"No subscribers found in {subscribers_file}. Nothing to do.")
        return

    seeded = 0
    skipped = 0
    for chat_id in subscribers:
        existing = list_entries(group_subscriptions_file, chat_id)
        if existing:
            print(f"  skip  {chat_id}: already has {len(existing)} group sub(s)")
            skipped += 1
            continue
        added = 0
        for group in DEFAULT_GROUPS:
            if add_entry(group_subscriptions_file, chat_id, group):
                added += 1
        print(f"  seed  {chat_id}: added {added}/{len(DEFAULT_GROUPS)} groups")
        seeded += 1

    print(f"\nDone. Seeded {seeded} chat(s); skipped {skipped} (already had group subs).")


if __name__ == '__main__':
    main()

from supabase import create_client
sb = create_client(
    'https://hdsntducurmhossannue.supabase.co',
    'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Imhkc250ZHVjdXJtaG9zc2FubnVlIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzczNjM0MTAsImV4cCI6MjA5MjkzOTQxMH0.aTghWk2f96wEVkVkmp0QlNoj274RKqJHKGLPu9F226s'
)

# Check content lengths across recent news
recent = sb.table('news').select('title,content,summary,entities,url,source').order('published_at', desc=True).limit(20).execute()

print("=== CONTENT LENGTH ANALYSIS (20 most recent) ===")
for i, r in enumerate(recent.data):
    title_len = len(r.get('title') or '')
    content_len = len(r.get('content') or '')
    has_summary = r.get('summary') not in (None, '', [])
    has_entities = r.get('entities') not in (None, '', [], {})
    has_url = r.get('url') not in (None, '')
    print(f"[{i+1}] source={r.get('source','?')[:20]} | title={title_len}c | content={content_len}c | summary={has_summary} | entities={has_entities} | url={has_url}")

# Show one full content example
print("\n=== FULL CONTENT SAMPLE ===")
for r in recent.data:
    if r.get('content') and len(r['content']) > 100:
        print(f"TITLE: {r['title']}")
        print(f"CONTENT ({len(r['content'])} chars): {r['content'][:500]}")
        break

# Check how many have non-null summary
summary_count = sb.table('news').select('id', count='exact').not_.is_('summary', 'null').execute()
entities_count = sb.table('news').select('id', count='exact').not_.is_('entities', 'null').execute()
url_count = sb.table('news').select('id', count='exact').not_.is_('url', 'null').execute()
content_check = sb.table('news').select('id', count='exact').not_.is_('content', 'null').execute()
print(f"\n=== NULL COUNTS (total 50559) ===")
print(f"non-null content: {content_check.count}")
print(f"non-null summary: {summary_count.count}")
print(f"non-null entities: {entities_count.count}")
print(f"non-null url: {url_count.count}")

# Sample entities structure
print("\n=== ENTITIES SAMPLE ===")
ent_sample = sb.table('news').select('entities,source').not_.is_('entities', 'null').limit(3).execute()
for r in ent_sample.data:
    print(f"source: {r['source']} | entities: {r['entities']}")

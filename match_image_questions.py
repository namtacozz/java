import json, sys
sys.stdout.reconfigure(encoding='utf-8')

with open('final_audited_questions.json', 'r', encoding='utf-8') as f:
    bench_qs = json.load(f)

with open('pdf_image_questions.json', 'r', encoding='utf-8') as f:
    pdf_imgs = json.load(f)

bench_image_qs = [q for q in bench_qs if q.get('image')]

print("=== All Benchmark Image Questions ===")
for q in bench_image_qs:
    opts = [o['text'][:25] for o in q['options']]
    print(f"ID {q['id']:3d} (orig {q.get('originalId', 'N/A'):3d}) | img: {q['image']:18s} | correct: {q['correctAnswers']} | opts: {opts[:2]}")

print("\n=== All PDF Image Questions ===")
for p in pdf_imgs:
    print(f"Page {p['page']:2d} | img size {str(p['img_size']):12s} | bullets: {p['bullet_count']} | correct: {p['correct_letters']} | opts: {[t[:25] for t in p['option_texts'][:2]]}")

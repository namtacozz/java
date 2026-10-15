import sys, json, re
sys.stdout.reconfigure(encoding='utf-8')

with open('sorted_questions.json', 'r', encoding='utf-8') as f:
    bench = json.load(f)
with open('live_google_forms_cards.json', 'r', encoding='utf-8') as f:
    live = json.load(f)

def norm(text):
    if not text: return ''
    return re.sub(r'\s+', ' ', text).strip().lower()

# Build score matrix
scores = []
for b_idx, b in enumerate(bench):
    b_opts = {o['label']: norm(o['text']) for o in b.get('options', [])}
    b_opts_set = set(b_opts.values())
    b_title = norm(b.get('title', ''))
    b_code = norm(b.get('code', ''))
    b_correct = b.get('correctAnswers', [])
    b_correct_texts = set([b_opts[k] for k in b_correct if k in b_opts])
    
    row = []
    for l_idx, l in enumerate(live):
        l_opts = [norm(o) for o in l.get('options', [])]
        l_opts_set = set(l_opts)
        l_title = norm(l.get('title', ''))
        l_correct_texts = set([norm(c) for c in l.get('correct', [])])
        
        # 1. Option match score
        intersection = b_opts_set.intersection(l_opts_set)
        score = 0
        
        if b_opts_set and l_opts_set:
            if b_opts_set == l_opts_set:
                score += 50
            else:
                score += len(intersection) * 10
                
        # 2. Title match
        if b_title and l_title:
            if b_title == l_title:
                score += 30
            elif b_title in l_title or l_title in b_title:
                score += 15
                
        # 3. Code in title
        if b_code and l_title and (b_code[:30] in l_title or l_title[:30] in b_code):
            score += 20
            
        # 4. Correct answer compatibility bonus
        if b_correct_texts and l_correct_texts and b_correct_texts == l_correct_texts:
            score += 5
            
        row.append(score)
    scores.append(row)

# Solve maximum weight bipartite matching or greedy assignment
# Since most are unique (score >= 50), let's do priority matching
import numpy as np

# We can use scipy linear_sum_assignment if available, or greedy
try:
    from scipy.optimize import linear_sum_assignment
    cost_matrix = -np.array(scores)
    bench_ind, live_ind = linear_sum_assignment(cost_matrix)
    assignments = list(zip(bench_ind, live_ind))
except Exception as e:
    print('scipy not available, using custom matching:', e)
    # Custom greedy by highest score
    edges = []
    for b_idx in range(len(bench)):
        for l_idx in range(len(live)):
            edges.append((scores[b_idx][l_idx], b_idx, l_idx))
    edges.sort(key=lambda x: x[0], reverse=True)
    
    assigned_b = set()
    assigned_l = set()
    assignments = []
    for score, b_idx, l_idx in edges:
        if b_idx not in assigned_b and l_idx not in assigned_l:
            assigned_b.add(b_idx)
            assigned_l.add(l_idx)
            assignments.append((b_idx, l_idx))

print(f"Total assignments: {len(assignments)}")

# Check each assignment
mismatches = []
for b_idx, l_idx in sorted(assignments, key=lambda x: bench[x[0]]['id']):
    b = bench[b_idx]
    l = live[l_idx]
    
    b_opts = {o['label']: norm(o['text']) for o in b.get('options', [])}
    b_correct = b.get('correctAnswers', [])
    b_correct_texts = [b_opts[k] for k in b_correct if k in b_opts]
    
    l_correct_texts = [norm(c) for c in l.get('correct', [])]
    
    # Check if correct answers match
    # Find expected keys in b
    expected_keys = []
    for k, v in b_opts.items():
        for c in l_correct_texts:
            if v == c:
                expected_keys.append(k)
    
    # If not exact match, check normalized or substring
    if not expected_keys:
        for k, v in b_opts.items():
            for c in l_correct_texts:
                if v in c or c in v:
                    expected_keys.append(k)
                    
    score = scores[b_idx][l_idx]
    if set(b_correct) != set(expected_keys) or score < 20:
        mismatches.append({
            'b_id': b['id'],
            'b_title': b.get('title'),
            'b_correct': b_correct,
            'b_correct_texts': b_correct_texts,
            'expected_keys': expected_keys,
            'l_idx': l_idx,
            'l_title': l.get('title'),
            'l_correct_texts': l_correct_texts,
            'score': score,
            'b_opts': [(o['label'], o['text']) for o in b.get('options', [])],
            'l_opts': l.get('options', [])
        })

print(f"Total answer mismatches: {len(mismatches)}")
for m in mismatches:
    print("="*60)
    print(f"Mismatch Q{m['b_id']}: {m['b_title']} (score {m['score']})")
    print(f"  Bench correct: {m['b_correct']} -> {m['b_correct_texts']}")
    print(f"  Live card #{m['l_idx']}: {m['l_title']}")
    print(f"  Live correct: {m['l_correct_texts']}")
    print(f"  Expected keys: {m['expected_keys']}")
    print(f"  Bench opts: {m['b_opts']}")
    print(f"  Live opts: {m['l_opts']}")

# Also show unassigned live cards (should be the 11 from ch 5 and 6)
assigned_live = set(l_idx for _, l_idx in assignments)
unassigned_live = [idx for idx in range(len(live)) if idx not in assigned_live]
print(f"\nUnassigned Live Cards ({len(unassigned_live)} cards):")
for idx in unassigned_live:
    card = live[idx]
    print(f"  Live #{idx}: title={card.get('title')[:50]} | opts={card.get('options')[:2]} | correct={card.get('correct')}")

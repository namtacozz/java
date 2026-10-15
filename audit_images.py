import sys, json, fitz, os
sys.stdout.reconfigure(encoding='utf-8')

doc = fitz.open('docs/Java - All.pdf')

with open('final_audited_questions.json', 'r', encoding='utf-8') as f:
    bench_qs = json.load(f)

# Find all cards in the PDF that have images
pdf_image_questions = []

for p_num in range(len(doc)):
    page = doc[p_num]
    imgs = page.get_images()
    content_imgs = []
    for img in imgs:
        xref = img[0]
        base_img = doc.extract_image(xref)
        if base_img['width'] > 100 and base_img['height'] > 50:
            content_imgs.append((xref, base_img))
            
    if content_imgs:
        # Check green checkmarks
        greens = []
        for d in page.get_drawings():
            if d.get('fill') and abs(d['fill'][0] - 0.1176) < 0.05 and abs(d['fill'][1] - 0.5569) < 0.05:
                if d['rect'].x0 > 200:
                    greens.append(d['rect'])
                    
        # Option blocks
        blocks = page.get_text('blocks')
        option_blocks = []
        for b in blocks:
            if abs(b[0] - 115.125) < 5:
                option_blocks.append(b)
                
        # Bullet rects
        bullets = []
        for d in page.get_drawings():
            r = d['rect']
            if abs(r.x0 - 92.25) < 2.0 and abs(r.width - 13.5) < 2.0 and abs(r.height - 13.5) < 2.0:
                bullets.append(r)
        bullets.sort(key=lambda b: b.y0)
        
        # Match bullets to greens
        correct_indices = []
        for g in greens:
            for b_idx, b in enumerate(bullets):
                if abs(b.y0 - g.y0) < 12:
                    correct_indices.append(b_idx)
        
        correct_letters = [chr(65 + i) for i in sorted(set(correct_indices))]
        
        pdf_image_questions.append({
            'page': p_num + 1,
            'doc_idx': p_num,
            'img_xref': content_imgs[0][0],
            'img_size': (content_imgs[0][1]['width'], content_imgs[0][1]['height']),
            'option_texts': [b[4].strip() for b in option_blocks],
            'bullet_count': len(bullets),
            'correct_letters': correct_letters,
            'first_line': page.get_text().split('\n')[0].strip() if page.get_text() else ''
        })

print(f"Total image questions found in PDF: {len(pdf_image_questions)}")

# Now let's compare with bench_qs questions that have image != null
bench_image_qs = [q for q in bench_qs if q.get('image')]
print(f"Total benchmark questions with image: {len(bench_image_qs)}")

with open('pdf_image_questions.json', 'w', encoding='utf-8') as f:
    json.dump(pdf_image_questions, f, ensure_ascii=False, indent=2)

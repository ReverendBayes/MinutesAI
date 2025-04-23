#!/usr/bin/env python3
import os
import argparse
import json
import re
import tempfile
import ffmpeg
import openai

def transcribe(input_path, whisper_model):
    tmp = tempfile.NamedTemporaryFile(suffix='.wav', delete=False)
    ffmpeg.input(input_path).output(tmp.name, ac=1, ar=16000).overwrite_output().run(quiet=True)
    with open(tmp.name, 'rb') as f:
        resp = openai.Audio.transcribe(whisper_model, f)
    os.unlink(tmp.name)
    return resp['text']

def chunk_text(text, max_chars):
    paragraphs = text.split('\n\n')
    chunks, current = [], ''
    for para in paragraphs:
        if len(current) + len(para) + 2 <= max_chars:
            current += para + '\n\n'
        else:
            if current:
                chunks.append(current.strip())
            if len(para) <= max_chars:
                current = para + '\n\n'
            else:
                for i in range(0, len(para), max_chars):
                    chunks.append(para[i:i+max_chars].strip())
                current = ''
    if current:
        chunks.append(current.strip())
    return chunks

def summarize_chunks(chunks, gpt_model):
    import json, re
    results = []
    for i, chunk in enumerate(chunks, start=1):
        messages = [
            {
                'role': 'system',
                'content': (
                    'You are a JSON-only summarizer. '
                    'Respond strictly with an array of objects, each containing: '
                    'summary (string), key_points (array of strings), '
                    'action_items (array of objects with assignee and task).'
                )
            },
            {'role': 'user', 'content': f'Text:\n{chunk}'}
        ]
        resp = openai.ChatCompletion.create(
            model=gpt_model, messages=messages, temperature=0, max_tokens=1000
        )
        raw = resp.choices[0].message.content.strip()
        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            m = re.search(r'\[.*\]', raw, re.S)
            if not m:
                print(f'Chunk {i}: failed to find JSON array. Raw start:\n{raw[:200]!r}')
                continue
            fragment = m.group(0)
            try:
                data = json.loads(fragment)
            except json.JSONDecodeError:
                print(f'Chunk {i}: invalid JSON after extraction. Fragment start:\n{fragment[:200]!r}')
                continue
        results.extend(data)
    return results

def merge_results(results):
    overview = ' '.join(r['summary'] for r in results)
    key_points = []
    for r in results:
        for kp in r.get('key_points', []):
            if kp not in key_points:
                key_points.append(kp)
    action_items = []
    seen = set()
    for r in results:
        for ai in r.get('action_items', []):
            key = (ai.get('assignee'), ai.get('task'))
            if key not in seen:
                seen.add(key)
                action_items.append(ai)
    return overview, key_points, action_items

def write_report(output_path, overview, key_points, action_items, transcript=None):
    with open(output_path, 'w') as f:
        f.write('# Meeting Summary\n\n')
        f.write('## Overview\n\n')
        f.write(overview + '\n\n')
        f.write('## Key Takeaways\n\n')
        for kp in key_points:
            f.write(f'- {kp}\n')
        f.write('\n## Action Items\n\n')
        for ai in action_items:
            assignee = ai.get('assignee', 'Unassigned')
            task = ai.get('task', '')
            f.write(f'- **{assignee}**: {task}\n')
        if transcript:
            f.write('\n## Full Transcript\n\n')
            f.write(transcript)
    print(f'Report written to {output_path}')

def main():
    parser = argparse.ArgumentParser(description='CLI Meeting Summarizer & Action-Item Generator')
    parser.add_argument('--input', '-i', required=True, help='Meeting audio/video file')
    parser.add_argument('--whisper-model', default='whisper-1', help='Whisper model for transcription')
    parser.add_argument('--gpt-model', default='gpt-4-turbo', help='GPT model for summarization')
    parser.add_argument('--max-chars', type=int, default=1200, help='Max chars per text chunk')
    parser.add_argument('--output', '-o', default='report.md', help='Output markdown report')
    parser.add_argument('--include-transcript', action='store_true', help='Append full transcript')
    parser.add_argument('--api-key', default=None, help='OpenAI API key')
    args = parser.parse_args()

    openai.api_key = args.api_key or os.getenv('OPENAI_API_KEY')
    if not openai.api_key:
        raise ValueError('OpenAI API key required. Use --api-key or set OPENAI_API_KEY.')

    print('Transcribing...')
    transcript = transcribe(args.input, args.whisper_model)
    print('Chunking transcript...')
    chunks = chunk_text(transcript, args.max_chars)
    print(f'{len(chunks)} chunks created. Summarizing...')
    results = summarize_chunks(chunks, args.gpt_model)
    overview, key_points, action_items = merge_results(results)
    write_report(args.output, overview, key_points, action_items,
                 transcript if args.include_transcript else None)

if __name__ == '__main__':
    main()

#!/usr/bin/env python3
"""Wrap mixed numeric expressions in <bdi dir="ltr"> so they survive RTL reordering.
    python3 scripts/bidi.py body_tpl.html body.html
Skips <style>, tags, td.num cells and existing <bdi>. Keeps balanced parentheses outside the isolate, never swallows
trailing punctuation. Arrows (→) are not fixable by isolation — gate.py rejects them; rewrite the sentence."""
import re, sys, pathlib
NUM = r'[+₪(]?\d(?:[\d,\.]*\d)?%?\)?'
PAT = re.compile(rf'(?<![\w/])(?<!\d-)({NUM}(?:\s?[–×÷−+/]\s?{NUM})+)(?![\w\-])')
SPLIT = re.compile(r'(<style>.*?</style>|<svg.*?</svg>|<td class="num[^"]*">.*?</td>|<bdi[^>]*>.*?</bdi>|<[^>]+>)', re.S)


def wrap(text):
    def rep(m):
        s = m.group(1); pre = post = ''
        if re.fullmatch(r'\d+/\d+', s): return s                       # gush/helka, plan numbers
        if s.count('(') > s.count(')') and s.startswith('('): pre, s = '(', s[1:]
        if s.count(')') > s.count('(') and s.endswith(')'): s, post = s[:-1], ')'
        if s.startswith('(') and s.endswith(')') and s.count('(') == 1: pre, s, post = '(', s[1:-1], ')'
        return f'{pre}<bdi dir="ltr" style="white-space:nowrap">{s}</bdi>{post}'
    return PAT.sub(rep, text)


def process(html):
    return ''.join(p if (not p or p.startswith('<')) else wrap(p) for p in SPLIT.split(html))


if __name__ == '__main__':
    src, dst = sys.argv[1], sys.argv[2]
    pathlib.Path(dst).write_text(process(pathlib.Path(src).read_text(encoding='utf-8')), encoding='utf-8')

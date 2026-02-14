#!/usr/bin/env python3
"""
STAGE 2: アカウント個別分析
12の分析軸で統計データを抽出
"""

import json
import sys
from collections import Counter
from datetime import datetime
import statistics

def load_data(filename):
    """JSONデータを読み込み"""
    with open(filename, 'r', encoding='utf-8') as f:
        return json.load(f)

def analyze_account(data, username):
    """12の分析軸で解析"""

    analysis = {
        'username': username,
        'total_posts': len(data),
        'analysis': {}
    }

    # 【1】構成パターン分布（簡易版 - 後で手動分類）
    line_counts = [p['line_count'] for p in data]
    analysis['analysis']['structure'] = {
        'avg_lines': statistics.mean(line_counts),
        'median_lines': statistics.median(line_counts),
        'line_distribution': Counter(line_counts).most_common(5)
    }

    # 【2】フック解析
    hook_types = [p['hook_type'] for p in data]
    hook_counter = Counter(hook_types)
    analysis['analysis']['hooks'] = {
        'distribution': dict(hook_counter),
        'top_hooks': hook_counter.most_common(3)
    }

    # 【3】文章リズム & ビジュアル構造
    char_counts = [p['char_count'] for p in data]
    newline_counts = [p['newline_count'] for p in data]

    analysis['analysis']['rhythm'] = {
        'avg_chars': statistics.mean(char_counts),
        'median_chars': statistics.median(char_counts),
        'min_chars': min(char_counts),
        'max_chars': max(char_counts),
        'avg_newlines': statistics.mean(newline_counts),
        'char_ranges': {
            '0-50': sum(1 for c in char_counts if c <= 50),
            '51-100': sum(1 for c in char_counts if 51 <= c <= 100),
            '101-150': sum(1 for c in char_counts if 101 <= c <= 150),
            '151-200': sum(1 for c in char_counts if 151 <= c <= 200),
            '201+': sum(1 for c in char_counts if c > 200)
        }
    }

    # 【4】感情トーン（簡易判定）
    # 後でGLM-5で詳細分析

    # 【5】テーマカテゴリ（後で手動分類）

    # 【6】CTA分析（簡易版）
    cta_keywords = ['保存', '覚えとけ', 'リプ', 'DM', 'コメント', 'フォロー', 'いいね', 'シェア']
    posts_with_cta = sum(1 for p in data if any(kw in p['text'] for kw in cta_keywords))
    analysis['analysis']['cta'] = {
        'posts_with_cta': posts_with_cta,
        'cta_rate': posts_with_cta / len(data) * 100
    }

    # 【7】投稿タイミング
    timestamps = [datetime.fromisoformat(p['created_at'].replace('Z', '+00:00')) for p in data]
    weekdays = Counter([t.weekday() for t in timestamps])
    hours = Counter([t.hour for t in timestamps])

    weekday_names = ['月', '火', '水', '木', '金', '土', '日']
    analysis['analysis']['timing'] = {
        'weekday_distribution': {weekday_names[k]: v for k, v in sorted(weekdays.items())},
        'hour_distribution': dict(sorted(hours.items())),
        'top_hours': hours.most_common(5)
    }

    # 【8】語彙分析（頻出キーワード）
    all_text = ' '.join([p['text'] for p in data])
    # 簡易版 - 後でより詳細な分析

    # 【9】アルゴリズム適性スコア
    for post in data:
        m = post
        post['algo_score'] = (
            m['likes'] * 1 +
            m['retweets'] * 3 +
            m['replies'] * 5 +
            m['bookmarks'] * 8
        ) / max(m['likes'] + m['retweets'] + m['replies'] + m['bookmarks'], 1) * 1000

        post['dwell_estimate'] = m['char_count'] * m['newline_count'] / 100

    algo_scores = [p['algo_score'] for p in data]
    analysis['analysis']['algorithm'] = {
        'avg_algo_score': statistics.mean(algo_scores),
        'median_algo_score': statistics.median(algo_scores)
    }

    # 【10】エンゲージメント相関
    likes = [p['likes'] for p in data]
    retweets = [p['retweets'] for p in data]
    replies = [p['replies'] for p in data]
    bookmarks = [p['bookmarks'] for p in data]

    analysis['analysis']['engagement'] = {
        'avg_likes': statistics.mean(likes),
        'avg_retweets': statistics.mean(retweets),
        'avg_replies': statistics.mean(replies),
        'avg_bookmarks': statistics.mean(bookmarks),
        'total_engagement': sum(likes) + sum(retweets) * 3 + sum(replies) * 5 + sum(bookmarks) * 8
    }

    # 【11】失敗パターン（下位20件）
    bottom_20 = sorted(data, key=lambda x: x['engagement_score'])[:20]
    analysis['analysis']['failures'] = {
        'bottom_20_avg_engagement': statistics.mean([p['engagement_score'] for p in bottom_20]),
        'bottom_20_avg_chars': statistics.mean([p['char_count'] for p in bottom_20])
    }

    # 【12】TOP10ポスト
    top_10 = sorted(data, key=lambda x: x['engagement_score'], reverse=True)[:10]
    analysis['top_10_posts'] = [
        {
            'text': p['text'],
            'likes': p['likes'],
            'retweets': p['retweets'],
            'replies': p['replies'],
            'bookmarks': p['bookmarks'],
            'engagement_score': p['engagement_score'],
            'char_count': p['char_count'],
            'hook_type': p['hook_type']
        }
        for p in top_10
    ]

    return analysis

def main():
    if len(sys.argv) < 2:
        print("Usage: python3 analyze_account.py <username>")
        sys.exit(1)

    username = sys.argv[1]
    input_file = f'/Users/od/2nd-Brain/03_知識ベース/マーケティング/X分析データ/{username}_raw_data.json'
    output_file = f'/Users/od/2nd-Brain/03_知識ベース/マーケティング/X分析データ/{username}_stats.json'

    print(f"📊 {username} の統計分析中...")

    data = load_data(input_file)
    analysis = analyze_account(data, username)

    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(analysis, f, ensure_ascii=False, indent=2)

    print(f"✅ 統計データ保存: {output_file}")
    print(f"📈 投稿数: {analysis['total_posts']}")
    print(f"📊 平均文字数: {analysis['analysis']['rhythm']['avg_chars']:.1f}")
    print(f"💬 平均いいね数: {analysis['analysis']['engagement']['avg_likes']:.1f}")

if __name__ == "__main__":
    main()

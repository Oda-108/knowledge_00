#!/usr/bin/env python3
"""
X分析マスター - データ収集スクリプト
競合アカウントの高エンゲージメントポストを収集
"""

import os
import json
import time
from datetime import datetime
import requests
from dotenv import load_dotenv

# 環境変数読み込み
load_dotenv('/Users/od/.twitter_api_keys.env')

BEARER_TOKEN = os.getenv('TWITTER_BEARER_TOKEN')

# 対象アカウント
TARGET_ACCOUNTS = {
    'Uncodeyansu': '栗松',
    'nero_sansei': 'ネロ先生',
    'develogon0': 'でべろごん'
}

def get_user_id(username):
    """ユーザー名からユーザーIDを取得"""
    url = f"https://api.twitter.com/2/users/by/username/{username}"
    headers = {"Authorization": f"Bearer {BEARER_TOKEN}"}

    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.json()['data']['id']
    else:
        print(f"Error getting user ID for {username}: {response.text}")
        return None

def get_user_tweets(user_id, username, max_results=100):
    """ユーザーのツイートを取得（最大100件）"""
    url = f"https://api.twitter.com/2/users/{user_id}/tweets"

    headers = {"Authorization": f"Bearer {BEARER_TOKEN}"}

    params = {
        'max_results': min(max_results, 100),  # API制限: 最大100
        'tweet.fields': 'created_at,public_metrics,entities,text',
        'exclude': 'retweets,replies'  # RTとリプライを除外
    }

    all_tweets = []

    while len(all_tweets) < max_results:
        response = requests.get(url, headers=headers, params=params)

        if response.status_code != 200:
            print(f"Error: {response.status_code} - {response.text}")
            break

        data = response.json()

        if 'data' not in data:
            break

        tweets = data['data']
        all_tweets.extend(tweets)

        print(f"取得済み: {len(all_tweets)}件 (@{username})")

        # 次のページがあるか確認
        if 'next_token' in data.get('meta', {}):
            params['pagination_token'] = data['meta']['next_token']
            time.sleep(1)  # レート制限対策
        else:
            break

    return all_tweets[:max_results]

def analyze_tweet_structure(text):
    """ツイートの構造を分析"""
    lines = text.split('\n')
    line_count = len(lines)

    # 改行数
    newline_count = text.count('\n')

    # フック手法の推定
    first_line = lines[0] if lines else ""

    hook_type = "不明"
    if any(char.isdigit() for char in first_line[:20]):
        hook_type = "衝撃数字"
    elif first_line.startswith(('なぜ', 'どう', 'どれ', '知ってる')):
        hook_type = "質問フック"
    elif '断言' in first_line or 'これが' in first_line:
        hook_type = "宣言フック"
    elif 'するな' in first_line or '嘘' in first_line:
        hook_type = "逆説フック"
    elif first_line.startswith(('正直', 'もう')):
        hook_type = "独白フック"

    return {
        'line_count': line_count,
        'newline_count': newline_count,
        'hook_type': hook_type
    }

def format_tweet_data(tweet, username):
    """ツイートデータを整形"""
    text = tweet['text']
    metrics = tweet['public_metrics']
    created_at = tweet['created_at']

    structure = analyze_tweet_structure(text)

    # メディア有無の判定
    has_media = 'attachments' in tweet
    media_type = "なし"
    if has_media:
        media_type = "画像/動画"

    return {
        'id': tweet['id'],
        'username': username,
        'text': text,
        'created_at': created_at,
        'char_count': len(text),
        'line_count': structure['line_count'],
        'newline_count': structure['newline_count'],
        'likes': metrics['like_count'],
        'retweets': metrics['retweet_count'],
        'replies': metrics['reply_count'],
        'bookmarks': metrics.get('bookmark_count', 0),
        'impressions': 0,  # ⚠️ API経由では取得不可、手動入力が必要
        'media': media_type,
        'hook_type': structure['hook_type'],
        'engagement_score': metrics['like_count'] + metrics['retweet_count'] * 3 + metrics['reply_count'] * 5
    }

def main():
    print("🚀 X分析マスター - データ収集開始\n")

    for username, display_name in TARGET_ACCOUNTS.items():
        print(f"\n{'='*50}")
        print(f"📊 {display_name} (@{username}) のデータ収集中...")
        print(f"{'='*50}\n")

        # ユーザーID取得
        user_id = get_user_id(username)
        if not user_id:
            print(f"⚠️ @{username} のユーザーIDが取得できませんでした")
            continue

        print(f"✅ ユーザーID: {user_id}\n")

        # ツイート取得
        tweets = get_user_tweets(user_id, username, max_results=100)

        if not tweets:
            print(f"⚠️ ツイートが取得できませんでした")
            continue

        # データ整形
        formatted_tweets = [format_tweet_data(tweet, username) for tweet in tweets]

        # エンゲージメントでソート
        formatted_tweets.sort(key=lambda x: x['engagement_score'], reverse=True)

        # JSON保存
        output_file = f'/Users/od/2nd-Brain/03_知識ベース/マーケティング/X分析データ/{username}_raw_data.json'
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(formatted_tweets, f, ensure_ascii=False, indent=2)

        print(f"\n✅ 保存完了: {output_file}")
        print(f"📈 取得件数: {len(formatted_tweets)}件\n")

        time.sleep(2)  # アカウント間の待機

    print("\n" + "="*50)
    print("🎉 全アカウントのデータ収集が完了しました！")
    print("="*50)
    print("\n⚠️ 注意: インプレッション数は手動で追加する必要があります")

if __name__ == "__main__":
    main()

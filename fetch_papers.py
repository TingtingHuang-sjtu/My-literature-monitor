#!/usr/bin/env python3
"""
文献监控工具 - 从 PubMed 抓取最新文献并推送到微信
"""

import requests
import xml.etree.ElementTree as ET
import json
import re
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path
from html import escape


def load_config(config_path="config.json"):
    """加载配置文件"""
    with open(config_path, "r", encoding="utf-8") as f:
        return json.load(f)


def build_journal_query(journals):
    """构建期刊查询语句"""
    journal_terms = [f'"{j}"[ta]' for j in journals]
    return "(" + " OR ".join(journal_terms) + ")"


def build_keyword_query(keyword_categories):
    """构建关键词查询语句"""
    all_keywords = []
    for cat_data in keyword_categories.values():
        all_keywords.extend(cat_data["keywords"])

    keyword_terms = [f'"{kw}"[tiab]' for kw in all_keywords]
    return "(" + " OR ".join(keyword_terms) + ")"


def search_pubmed(query, max_results=200, lookback_days=3):
    """搜索 PubMed"""
    base_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"

    date_threshold = (datetime.now() - timedelta(days=lookback_days)).strftime("%Y/%m/%d")
    full_query = f"({query}) AND {date_threshold}[edat] : 3000[edat]"

    search_url = f"{base_url}/esearch.fcgi"
    search_params = {
        "db": "pubmed",
        "term": full_query,
        "retmax": max_results,
        "retmode": "xml",
        "sort": "date",
    }

    try:
        response = requests.get(search_url, params=search_params, timeout=60)
        response.raise_for_status()
        return response.text
    except requests.RequestException as e:
        print(f"❌ PubMed 搜索失败: {e}")
        return None


def parse_articles(xml_data):
    """解析 PubMed XML 结果"""
    if not xml_data:
        return []

    try:
        root = ET.fromstring(xml_data)
    except ET.ParseError as e:
        print(f"❌ XML 解析失败: {e}")
        return []

    articles = []
    for article_elem in root.findall(".//PubmedArticle"):
        pmid_elem = article_elem.find(".//PMID")
        if pmid_elem is None:
            continue

        pmid = pmid_elem.text
        title_elem = article_elem.find(".//ArticleTitle")
        title = title_elem.text if title_elem is not None else "No title"

        abstract_parts = []
        for abstract_text in article_elem.findall(".//AbstractText"):
            label = abstract_text.get("Label", "")
            text = "".join(abstract_text.itertext())
            if label:
                abstract_parts.append(f"{label}: {text}")
            else:
                abstract_parts.append(text)
        abstract = " ".join(abstract_parts)

        journal_elem = article_elem.find(".//Journal/Title")
        journal = journal_elem.text if journal_elem is not None else "Unknown Journal"

        pub_date_parts = []
        for part in ["Year", "Month", "Day"]:
            elem = article_elem.find(f".//PubDate/{part}")
            if elem is not None:
                pub_date_parts.append(elem.text)
        pub_date = " ".join(pub_date_parts) if pub_date_parts else "Unknown date"

        authors = []
        for author_elem in article_elem.findall(".//Author"):
            last = author_elem.find("LastName")
            fore = author_elem.find("ForeName")
            if last is not None and fore is not None:
                authors.append(f"{fore.text} {last.text}")
            elif last is not None:
                authors.append(last.text)

        doi = ""
        for aid_elem in article_elem.findall(".//ArticleId"):
            if aid_elem.get("IdType") == "doi":
                doi = aid_elem.text
                break

        articles.append(
            {
                "pmid": pmid,
                "title": title,
                "abstract": abstract,
                "journal": journal,
                "pub_date": pub_date,
                "authors": ", ".join(authors[:5]) + ("..." if len(authors) > 5 else ""),
                "doi": doi,
            }
        )

    return articles


def match_keywords(text, keyword_categories):
    """检查文本匹配哪些关键词类别"""
    text_lower = text.lower()
    matched = {}

    for cat_id, cat_data in keyword_categories.items():
        matched_keywords = []
        for kw in cat_data["keywords"]:
            pattern = r"\b" + re.escape(kw.lower()) + r"\b"
            if re.search(pattern, text_lower):
                matched_keywords.append(kw)

        if matched_keywords:
            matched[cat_id] = {
                "label": cat_data["label"],
                "keywords": matched_keywords,
            }

    return matched


def generate_html_report(articles_by_category, date_str):
    """生成 HTML 报告"""
    html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>文献简报 - {date_str}</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
            line-height: 1.6;
            color: #333;
            background: #f5f5f5;
            padding: 20px;
        }}
        .container {{
            max-width: 900px;
            margin: 0 auto;
            background: white;
            padding: 30px;
            border-radius: 8px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }}
        h1 {{
            color: #2c3e50;
            border-bottom: 3px solid #3498db;
            padding-bottom: 15px;
            margin-bottom: 25px;
        }}
        .summary {{
            background: #ecf0f1;
            padding: 15px;
            border-radius: 5px;
            margin-bottom: 30px;
        }}
        .category {{
            margin-bottom: 40px;
        }}
        .category h2 {{
            color: #34495e;
            background: #3498db;
            color: white;
            padding: 12px 18px;
            border-radius: 5px;
            margin-bottom: 20px;
        }}
        .article {{
            border-left: 4px solid #3498db;
            padding: 15px 20px;
            margin-bottom: 20px;
            background: #fafafa;
            border-radius: 0 5px 5px 0;
        }}
        .article h3 {{
            color: #2c3e50;
            margin-bottom: 10px;
        }}
        .article h3 a {{
            color: #2c3e50;
            text-decoration: none;
        }}
        .article h3 a:hover {{
            color: #3498db;
        }}
        .meta {{
            color: #7f8c8d;
            font-size: 0.9em;
            margin-bottom: 10px;
        }}
        .keywords {{
            margin-top: 10px;
        }}
        .keyword {{
            display: inline-block;
            background: #3498db;
            color: white;
            padding: 3px 10px;
            border-radius: 12px;
            font-size: 0.85em;
            margin-right: 6px;
            margin-top: 4px;
        }}
        .abstract {{
            margin-top: 12px;
            padding: 12px;
            background: white;
            border-radius: 4px;
            font-size: 0.95em;
            color: #555;
        }}
        .footer {{
            margin-top: 40px;
            padding-top: 20px;
            border-top: 2px solid #ecf0f1;
            text-align: center;
            color: #95a5a6;
            font-size: 0.9em;
        }}
        @media (max-width: 768px) {{
            .container {{ padding: 15px; }}
            body {{ padding: 10px; }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>📚 文献简报 - {date_str}</h1>
"""

    total_count = sum(len(arts) for arts in articles_by_category.values())
    html += f"""
        <div class="summary">
            <strong>📊 本期概览</strong><br>
            共发现 <strong>{total_count}</strong> 篇相关文献
        </div>
"""

    for cat_id, articles in articles_by_category.items():
        if not articles:
            continue

        label = articles[0]["category_label"] if articles else cat_id
        html += f"""
        <div class="category">
            <h2>{escape(label)} ({len(articles)} 篇)</h2>
"""

        for article in articles:
            doi_url = f"https://doi.org/{article['doi']}" if article["doi"] else "#"
            pubmed_url = f"https://pubmed.ncbi.nlm.nih.gov/{article['pmid']}/"

            html += f"""
            <div class="article">
                <h3><a href="{doi_url}" target="_blank">{escape(article['title'])}</a></h3>
                <div class="meta">
                    <strong>期刊:</strong> {escape(article['journal'])} |
                    <strong>日期:</strong> {escape(article['pub_date'])} |
                    <strong>PMID:</strong> <a href="{pubmed_url}" target="_blank">{article['pmid']}</a>
                </div>
                <div class="meta">
                    <strong>作者:</strong> {escape(article['authors'])}
                </div>
                <div class="keywords">
                    <strong>匹配关键词:</strong>
"""

            for kw in article["matched_keywords"]:
                html += f'<span class="keyword">{escape(kw)}</span>'

            html += "</div>"

            if article["abstract"]:
                html += f"""
                <div class="abstract">
                    <strong>摘要:</strong> {escape(article['abstract'][:500])}{"..." if len(article['abstract']) > 500 else ""}
                </div>
"""

            html += """
            </div>
"""

        html += """
        </div>
"""

    html += f"""
        <div class="footer">
            <p>Generated by 文献监控工具 | {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        </div>
    </div>
</body>
</html>
"""

    return html


def send_wechat_notification(articles_by_category, date_str, sendkey):
    """通过 Server酱 发送微信通知"""
    if not sendkey:
        print("⚠️  未配置 Server酱 SendKey，跳过微信推送")
        return False

    total_count = sum(len(arts) for arts in articles_by_category.values())

    title = f"📚 文献简报 {date_str} - 共 {total_count} 篇新文献"

    body_parts = [f"## 📚 文献简报 {date_str}\n", f"**共发现 {total_count} 篇相关文献**\n"]

    for cat_id, articles in articles_by_category.items():
        if not articles:
            continue

        label = articles[0]["category_label"] if articles else cat_id
        body_parts.append(f"\n### {label} ({len(articles)} 篇)\n")

        for i, article in enumerate(articles[:5], 1):
            doi_link = f"https://doi.org/{article['doi']}" if article["doi"] else ""
            body_parts.append(
                f"{i}. **{article['title']}**\n"
                f"   - {article['journal']} | {article['pub_date']}\n"
                f"   - [查看文献]({doi_link})\n"
            )

        if len(articles) > 5:
            body_parts.append(f"\n*... 还有 {len(articles) - 5} 篇文献*\n")

    body_parts.append("\n---\n*完整报告请查看 GitHub 仓库*")

    body = "\n".join(body_parts)

    try:
        response = requests.post(
            f"https://sctapi.ftqq.com/{sendkey}.send",
            data={"title": title, "desp": body},
            timeout=30,
        )
        result = response.json()

        if result.get("code") == 0:
            print("✅ 微信推送成功")
            return True
        else:
            print(f"❌ 微信推送失败: {result.get('message', 'Unknown error')}")
            return False
    except requests.RequestException as e:
        print(f"❌ 微信推送失败: {e}")
        return False


def main():
    """主函数"""
    print("=" * 60)
    print("📚 文献监控工具启动")
    print("=" * 60)

    config_path = os.environ.get("CONFIG_PATH", "config.json")
    output_dir = os.environ.get("OUTPUT_DIR", "reports")

    config = load_config(config_path)
    journals = config["journals"]
    keyword_categories = config["keyword_categories"]
    lookback_days = config.get("lookback_days", 3)
    max_results = config.get("max_results_per_query", 200)
    sendkey = os.environ.get("SERVERCHAN_SENDKEY", config.get("serverchan_sendkey", ""))

    print(f"\n📖 监控 {len(journals)} 本期刊")
    print(f"🔍 搜索最近 {lookback_days} 天的文献")

    journal_query = build_journal_query(journals)
    keyword_query = build_keyword_query(keyword_categories)
    full_query = f"{journal_query} AND {keyword_query}"

    print("\n🔎 正在搜索 PubMed...")
    xml_data = search_pubmed(full_query, max_results=max_results, lookback_days=lookback_days)

    if xml_data is None:
        print("❌ 搜索失败，退出")
        sys.exit(1)

    print("📄 正在解析结果...")
    articles = parse_articles(xml_data)
    print(f"找到 {len(articles)} 篇文献")

    articles_by_category = {cat_id: [] for cat_id in keyword_categories.keys()}
    seen_pmids = set()

    for article in articles:
        if article["pmid"] in seen_pmids:
            continue

        text_to_check = f"{article['title']} {article['abstract']}"
        matched = match_keywords(text_to_check, keyword_categories)

        if matched:
            seen_pmids.add(article["pmid"])

            for cat_id, match_info in matched.items():
                article_copy = article.copy()
                article_copy["matched_keywords"] = match_info["keywords"]
                article_copy["category_label"] = match_info["label"]
                articles_by_category[cat_id].append(article_copy)

    print("\n📊 分类统计:")
    for cat_id, arts in articles_by_category.items():
        label = keyword_categories[cat_id]["label"]
        print(f"  - {label}: {len(arts)} 篇")

    date_str = datetime.now().strftime("%Y-%m-%d")
    html_report = generate_html_report(articles_by_category, date_str)

    Path(output_dir).mkdir(parents=True, exist_ok=True)

    report_path = os.path.join(output_dir, f"report_{date_str}.html")
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(html_report)
    print(f"\n✅ 报告已保存: {report_path}")

    latest_path = os.path.join(output_dir, "latest.html")
    with open(latest_path, "w", encoding="utf-8") as f:
        f.write(html_report)

    if sendkey:
        print("\n📱 正在发送微信通知...")
        send_wechat_notification(articles_by_category, date_str, sendkey)

    print("\n" + "=" * 60)
    print("✅ 任务完成")
    print("=" * 60)


if __name__ == "__main__":
    main()
